from __future__ import annotations

import logging
from typing import TypedDict, Annotated
from dotenv import load_dotenv

# Ensure environment variables (.env) are loaded up front
load_dotenv()

logger = logging.getLogger(__name__)

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI

from .tools.rag import rag_tool
from .tools.search import tavily_tool
from .tools.pdf_extractor import pdf_extraction_tool
from .tools.web_scraper import web_page_tool
from .tools.unanswered import save_unanswered_question
from .prompts import AGENT_SYSTEM_PROMPT

class AgentState(TypedDict):
    """The current state of the agent."""
    messages: Annotated[list[BaseMessage], add_messages]

# Define the tools array including RAG, Tavily, PDF extraction, and unanswered question saver
tools = [rag_tool, tavily_tool, web_page_tool, pdf_extraction_tool, save_unanswered_question]
tool_node = ToolNode(tools)

# Initialize the OpenAI model (gpt-5.4-mini: fast, cost-effective, supports tool calls)
model = ChatOpenAI(model="gpt-5.4-mini", temperature=0).bind_tools(tools)

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

# Human-readable labels for each tool the agent can call
_TOOL_LABELS: dict[str, str] = {
    "tavily_tool": "Searching Yarmouk University website…",
    "rag_tool": "Retrieving from knowledge base…",
    "web_page_tool": "Reading university web page…",
    "pdf_extraction_tool": "Extracting PDF document…",
    "save_unanswered_question": "Logging unanswered question…",
}


async def stream_agent(graph, query: str, thread_id: str):
    """Yield structured SSE events: {type, label|text} dicts."""
    inputs = {"messages": [HumanMessage(content=query)]}
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 20,
    }

    try:
        async for event in graph.astream_events(inputs, config=config, version="v2"):
            kind = event["event"]

            if kind == "on_tool_start":
                tool_name = event.get("name", "")
                label = _TOOL_LABELS.get(tool_name, f"Running {tool_name}…")
                logger.info("Tool started: %s", tool_name)
                yield {"type": "status", "label": label}

            elif kind == "on_tool_end":
                logger.info("Tool finished: %s", event.get("name", ""))
                # Return to generic thinking state between tool calls
                yield {"type": "status", "label": "Thinking…"}

            elif kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                content = chunk.content
                if isinstance(content, str) and content:
                    yield {"type": "token", "text": content}

    except Exception as e:
        logger.exception("Unexpected error during agent stream")
        yield {"type": "error", "text": f"❌ Unexpected error: {e}"}
