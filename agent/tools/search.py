from __future__ import annotations

import logging
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

logger = logging.getLogger(__name__)

# Restrict Tavily exclusively to the official Yarmouk University domain.
# NOTE: Do NOT add "site:yu.edu.jo" to the query string as well — combining
# include_domains with a site: operator can produce zero results from the API.
_tavily = TavilySearch(
    max_results=5,
    include_domains=["yu.edu.jo"],
)


@tool
def tavily_tool(query: str) -> str:
    """
    Official Yarmouk University Search Tool.
    USE THIS TOOL to find the latest university news, policies, academic
    calendars, announcements, and faculty information from yu.edu.jo.
    Input should be a clear, concise search query in Arabic or English.
    """
    logger.info("Tavily search: %s", query)
    try:
        results = _tavily.invoke({"query": query})
        if not results:
            return "No results found on yu.edu.jo for that query."
        # Format as a numbered list for readability
        lines = []
        for i, r in enumerate(results, 1):
            url = r.get("url", "")
            content = r.get("content", "").strip()
            lines.append(f"{i}. {url}\n   {content}")
        return "\n\n".join(lines)
    except Exception as e:
        logger.exception("Tavily search failed")
        return f"Search Error: {e}"
