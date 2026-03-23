"""
Agent tool: save_unanswered_question

When the agent cannot find an answer to a university-related question after
exhausting search and RAG tools, it calls this tool to flag the question for
a human admin to answer later via the dashboard.

The tool writes directly to the PostgreSQL `unanswered_questions` table.
"""

from __future__ import annotations

import os
import logging
import psycopg

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")


@tool
def save_unanswered_question(question: str, language: str = "ar", thread_id: str = "") -> str:
    """
    Save a university-related question that you could NOT answer.
    USE THIS TOOL when:
    - You searched with tavily_tool and found no relevant results
    - The question IS about Yarmouk University but you lack the information
    - You want a human admin to provide the answer later

    DO NOT use this tool for:
    - Questions unrelated to the university (just refuse those politely)
    - Questions you CAN answer from search results

    Args:
        question: The exact user question that could not be answered
        language: The language of the question ('ar' for Arabic, 'en' for English)
        thread_id: The conversation thread ID (optional)
    """
    logger.info("Saving unanswered question: %s", question[:100])
    try:
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            conn.execute(
                """INSERT INTO unanswered_questions (question, language, thread_id)
                   VALUES (%s, %s, %s)""",
                (question, language, thread_id),
            )
        return (
            "Question saved successfully. A university admin will review and answer it soon. "
            "Please inform the user that their question has been forwarded to the university team."
        )
    except Exception as e:
        logger.exception("Failed to save unanswered question")
        return f"Failed to save the question: {e}. Please inform the user to try again later."
