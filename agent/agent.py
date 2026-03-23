from __future__ import annotations

import logging
from typing import TypedDict, Annotated
from google.genai.errors import ClientError
from dotenv import load_dotenv

# Ensure environment variables (.env) are loaded up front
load_dotenv()

logger = logging.getLogger(__name__)

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_google_genai import ChatGoogleGenerativeAI

from .tools.rag import rag_tool
from .tools.search import tavily_tool
from .prompts import AGENT_SYSTEM_PROMPT

class AgentState(TypedDict):
    """The current state of the agent."""
    messages: Annotated[list[BaseMessage], add_messages]

# Define the tools array including both RAG and Tavily
tools = [rag_tool, tavily_tool]
tool_node = ToolNode(tools)

# Initialize the Gemini model
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0).bind_tools(tools)

# System message singleton — defined once and prepended only when missing
_SYSTEM_MSG = SystemMessage(content=AGENT_SYSTEM_PROMPT)


def call_model(state: AgentState) -> dict:
    """Invoke the LLM with optional tool bindings, injecting system prompt if absent."""
    messages = state["messages"]

    # Prepend system prompt only when it is not already the first stored message.
    # LangGraph's add_messages reducer keeps the full history, so after the first
    # turn the SystemMessage will already be at index 0 — no need to re-inject.
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [_SYSTEM_MSG, *messages]

    logger.debug("Invoking model with %d messages", len(messages))
    response = model.invoke(messages)
    return {"messages": [response]}

def compile_graph(checkpointer=None):
    """Build and compile the graph, optionally attaching persistent memory."""
    builder = StateGraph(AgentState)
    builder.add_node("agent", call_model)
    builder.add_node("tools", tool_node)
    
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    
    # Compile into a runnable graph with the provided memory checkpointer
    return builder.compile(checkpointer=checkpointer)

# Streaming generator function
async def stream_agent(graph, query: str, thread_id: str):
    """Stream the responses from the agent via astream_events using REST yielding chunks."""
    inputs = {"messages": [HumanMessage(content=query)]}
    
    # Send the thread_id config and enforcing the 20 steps recursion limit
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 20
    }
    
    try:
        # Streaming both tool events and model output tokens
        async for event in graph.astream_events(inputs, config=config, version="v2"):
            kind = event["event"]

            # Show a single friendly status pill while any tool is running
            if kind == "on_tool_start":
                logger.info("Tool started: %s", event["name"])
                yield "[SYSTEM_STATUS] Thinking…\n"

            elif kind == "on_tool_end":
                logger.info("Tool finished: %s", event["name"])
                # Intentionally silent — no extra pill on completion

            # Stream individual LLM output tokens
            elif kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                # content can be str or list (tool-use chunks) — only yield plain text
                content = chunk.content
                if isinstance(content, str) and content:
                    yield content

    except ClientError as e:
        if e.code == 429:
            logger.warning("Gemini API rate limit hit: %s", e)
            yield (
                "⚠️ **API rate limit reached.** The free-tier daily quota for this "
                "model has been exhausted. Please wait until the quota resets (usually "
                "midnight Pacific time) or upgrade to a paid plan."
            )
        else:
            logger.exception("Gemini API client error")
            yield f"❌ **API error ({e.code}):** {e}"
    except Exception as e:
        logger.exception("Unexpected error during agent stream")
        yield f"❌ **Unexpected error:** {e}"
