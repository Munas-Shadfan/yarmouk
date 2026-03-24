"""
RAG tool — semantic search over the Yarmouk University vector knowledge base.
This is ALWAYS the first tool the agent calls. Live web access is a fallback only.
"""
from __future__ import annotations
import logging

from langchain_core.tools import tool

from .knowledge_base import search_knowledge

logger = logging.getLogger(__name__)


@tool
async def rag_tool(query: str) -> str:
    """
    Search the Yarmouk University knowledge base (vector database).

    *** ALWAYS CALL THIS FIRST before any other tool. ***

    The knowledge base contains pre-indexed, up-to-date content from ALL yu.edu.jo
    pages and PDFs, including:
      - Academic calendars and semester dates (admreg.yu.edu.jo)
      - Admission and registration procedures
      - Available majors and academic programs
      - Graduation requirements and instructions
      - University rules, regulations and bylaws
      - Hussein bin Talal Library resources
      - Queen Rania Center training courses and diplomas
      - Job vacancies and scholarships (hr.yu.edu.jo)
      - Staff contacts and phone directories
      - University news and announcements

    If the results have relevance ≥ 28%, use them to answer the user directly.
    Only fall back to web_page_tool / pdf_extraction_tool when this tool returns
    the "No relevant content found" message.

    Args:
        query: The user question or keywords (Arabic or English)
    """
    results = await search_knowledge(query, k=6)

    if not results:
        return (
            "⚠️ KNOWLEDGE BASE MISS — no relevant content found for this query.\n"
            "→ You MUST now call web_page_tool to fetch live content from yu.edu.jo.\n"
            "Any content you scrape will be auto-indexed so future questions are answered instantly."
        )

    header = f"Found {len(results)} relevant knowledge chunks:\n\n"
    chunks = []
    for i, r in enumerate(results, 1):
        score_pct = int(r["score"] * 100)
        chunks.append(
            f"Source [{i}]: {r['url']} ({r['type']}, relevance {score_pct}%)\n"
            f"Content: {r['content']}\n---"
        )
    return header + "\n".join(chunks)
