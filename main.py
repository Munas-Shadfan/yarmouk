import os
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

from agent.agent import compile_graph, stream_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

DATABASE_URL = os.getenv("DATABASE_URL", "")

import sys
import asyncio

# On Windows, psycopg async requires the SelectorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Manage the asynchronous PostgreSQL checkpointer and connection pool in FastAPI context limits
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Establish persistent robust database connectivity
    if not DATABASE_URL:
        logger.error("DATABASE_URL is not set!")
        raise ValueError("DATABASE_URL is not set")

    logger.info("Connecting to database: %s", DATABASE_URL.split("@")[-1]) # Log only host for security
    
    pool = AsyncConnectionPool(
        conninfo=DATABASE_URL,
        min_size=1,
        max_size=2,
        open=False,  # open manually so we can await it
        check=True,  # verify connection is alive before providing it from pool
        kwargs={"autocommit": True, "row_factory": dict_row},
    )
    
    try:
        await pool.open(wait=True, timeout=30)
        logger.info("Database connection pool opened successfully")
    except Exception as e:
        logger.error("Failed to open database connection pool: %s", e)
        # We don't want the server to start without a DB if it's critical
        raise
    
    # Set up our persistent memory saver
    checkpointer = AsyncPostgresSaver(pool)
    
    # Bootstrap tables if this is the first execution
    await checkpointer.setup()
    
    # Attach compiled agent ready to be accessed globally
    app.state.graph = compile_graph(checkpointer)
    
    yield
    
    # Clean up standard async pool
    await pool.close()

app = FastAPI(lifespan=lifespan)

# Use absolute path to guarantee the templates directory is found
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

class ChatRequest(BaseModel):
    query: str
    thread_id: str = "default_session"

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface(request: Request):
    """Serve the modern web chat interface from Jinja template."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/history")
async def get_history():
    """Fetch all unique thread IDs from the checkpoints table."""
    graph = app.state.graph
    # Access the checkpointer from the graph (if available)
    # LangGraph's AsyncPostgresSaver doesn't have a direct 'list_threads' yet in all versions
    # but we can query the pool directly as it's attached to the app state or accessible via checkpointer
    checkpointer = graph.checkpointer
    if not checkpointer or not hasattr(checkpointer, 'conn_pool'):
        return {"threads": []}
    
    async with checkpointer.conn_pool.connection() as conn:
        async with conn.cursor() as cur:
            # Query unique thread IDs and the latest checkpoint time
            await cur.execute("""
                SELECT thread_id, MAX(checkpoint_id) as last_id
                FROM checkpoints
                GROUP BY thread_id
                ORDER BY last_id DESC
                LIMIT 50
            """)
            rows = await cur.fetchall()
            return {"threads": [row["thread_id"] for row in rows]}

@app.get("/api/messages/{thread_id}")
async def get_messages(thread_id: str):
    """Fetch all messages for a specific thread."""
    graph = app.state.graph
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    
    messages = []
    if state and "messages" in state.values:
        for msg in state.values["messages"]:
            # Format message for frontend
            msg_type = "user" if isinstance(msg, HumanMessage) else "ai"
            if isinstance(msg, SystemMessage): continue # Skip system messages
            
            # Extract content string
            content = msg.content
            if not isinstance(content, str): continue # Skip complex content for now
            
            messages.append({
                "role": msg_type,
                "content": content
            })
    
    return {"messages": messages}

@app.post("/api/chat")
async def chat_stream(request: ChatRequest):
    """REST API endpoint using Server-Sent Events (SSE) for streaming LangGraph iterations."""
    graph = app.state.graph
    
    async def sse_generator():
        try:
            # We yield chunks strictly formatted for SSE standard protocol.
            async for chunk in stream_agent(graph, request.query, request.thread_id):
                # JSON payload guarantees clean formatting when streaming arbitrary tokens.
                yield f"data: {json.dumps({'content': chunk})}\n\n"
                
            # Signal frontend that string stream completion has occurred.
            yield f"data: {json.dumps({'content': '[DONE]'})}\n\n"
        except Exception as e:
            logger.exception("Error during agent SSE stream")
            yield f"data: {json.dumps({'content': f'[Error]: {e}'})}\n\n"
            yield f"data: {json.dumps({'content': '[DONE]'})}\n\n"
            
    return StreamingResponse(sse_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
