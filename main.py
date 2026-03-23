import os
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from psycopg_pool import AsyncConnectionPool
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

from agent.agent import compile_graph, stream_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from psycopg.rows import dict_row

from db import init_admin_schema
from auth import seed_default_admin
from admin_routes import router as admin_router
from agent.tools.knowledge_base import set_pool as kb_set_pool
from agent.tools.indexer import run_initial_indexing

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

    # Pool for LangGraph checkpointer — must use autocommit=True
    pool = AsyncConnectionPool(
        conninfo=DATABASE_URL,
        min_size=1,
        max_size=10,
        open=False,
        kwargs={"autocommit": True},
    )

    # Separate pool for knowledge base (RAG search + save) — avoids
    # "another command is already in progress" caused by LangGraph holding
    # a checkpointer connection open while KB tasks try to embed+insert.
    kb_pool = AsyncConnectionPool(
        conninfo=DATABASE_URL,
        min_size=2,
        max_size=10,
        open=False,
        kwargs={"autocommit": True},
    )

    try:
        await pool.open(wait=True, timeout=30)
        await kb_pool.open(wait=True, timeout=30)
        logger.info("Database connection pools opened successfully")
    except Exception as e:
        logger.error("Failed to open database connection pool: %s", e)
        raise

    # Set up our persistent memory saver
    checkpointer = AsyncPostgresSaver(pool)

    # Bootstrap tables if this is the first execution
    await checkpointer.setup()

    # Initialize admin tables and seed default admin user
    await init_admin_schema(pool)
    await seed_default_admin(pool)
    logger.info("Admin schema initialized, default admin seeded")

    # Attach pool and compiled agent to app state
    app.state.pool = pool
    app.state.graph = compile_graph(checkpointer)

    # Wire the DEDICATED knowledge base pool so rag_tool can search & save
    # without interfering with LangGraph's checkpointer transactions.
    kb_set_pool(kb_pool)
    logger.info("Knowledge base pool wired (dedicated pool)")

    # Trigger initial indexing in the background (idempotent — skips if already done)
    # Pass force=True the first time to ensure all KEY_PAGES and KNOWN_PDFS are indexed.
    # Once the DB has chunks, subsequent restarts skip automatically.
    async def _background_index():
        try:
            result = await run_initial_indexing(force=False)
            logger.info("Background indexing result: %s", result)
        except Exception:
            logger.exception("Background indexing failed")

    asyncio.create_task(_background_index())

    yield

    # Clean up both pools
    await pool.close()
    await kb_pool.close()

app = FastAPI(lifespan=lifespan)

# Use absolute path to guarantee the templates directory is found
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Serve static files (logo, images, etc.)
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Mount admin API router
app.include_router(admin_router, prefix="/admin/api")


class ChatRequest(BaseModel):
    query: str
    thread_id: str = "default_session"


# ---------------------------------------------------------------------------
# Admin page routes (serve HTML, no auth — auth is client-side via JWT)
# ---------------------------------------------------------------------------

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin_login.html")


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin_dashboard.html")


# ---------------------------------------------------------------------------
# Chat routes (existing)
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def get_showcase(request: Request):
    """Integration layout showcase — navigation hub for 3 embedding patterns."""
    return templates.TemplateResponse(request=request, name="showcase.html")

@app.get("/chat", response_class=HTMLResponse)
async def get_chat_interface(request: Request):
    """Serve the main full-screen chat interface."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/demo/fullscreen", response_class=HTMLResponse)
async def demo_fullscreen(request: Request):
    """Demo: Pattern 01 — Full-screen dedicated chat page with history sidebar."""
    return templates.TemplateResponse(request=request, name="demo_fullscreen.html")

@app.get("/demo/floating", response_class=HTMLResponse)
async def demo_floating(request: Request):
    """Demo: Pattern 02 — Floating bottom-right chat bubble on a fake university page."""
    return templates.TemplateResponse(request=request, name="demo_floating.html")

@app.get("/demo/copilot", response_class=HTMLResponse)
async def demo_copilot(request: Request):
    """Demo: Pattern 03 — Right-sidebar AI copilot on a student portal dashboard."""
    return templates.TemplateResponse(request=request, name="demo_copilot.html")

@app.get("/api/history")
async def get_history():
    """Fetch all unique thread IDs from the checkpoints table."""
    graph = app.state.graph
    # Access the checkpointer from the graph (if available)
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
    pool = app.state.pool

    async def sse_generator():
        _tools_used: list[str] = []
        _response_len: int = 0

        try:
            # stream_agent yields structured dicts: {type, label|text}
            async for event in stream_agent(graph, request.query, request.thread_id):
                yield f"data: {json.dumps(event)}\n\n"
                # Track which tools fired (status events carry the label)
                if event.get("type") == "status":
                    label = event.get("label", "").lower()
                    for t in ("web_page_tool", "pdf_extraction_tool",
                              "tavily_tool", "rag_tool", "save_unanswered_question"):
                        if t.replace("_", " ").split()[0] in label and t not in _tools_used:
                            _tools_used.append(t)
                elif event.get("type") == "token":
                    _response_len += len(event.get("text", ""))
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            logger.exception("Error during agent SSE stream")
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        # Log analytics (fire-and-forget, don't block the response)
        try:
            async with pool.connection() as conn:
                await conn.execute(
                    "INSERT INTO chat_analytics (thread_id, user_query, response_length, tools_used) VALUES (%s, %s, %s, %s)",
                    (request.thread_id, request.query[:500], _response_len, _tools_used),
                )
        except Exception:
            logger.warning("Failed to log chat analytics", exc_info=True)

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
