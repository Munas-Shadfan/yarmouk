"""
Admin API router — all endpoints require JWT authentication.
Mounted at /admin/api in main.py.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from auth import (
    Token,
    AdminUser,
    TokenData,
    authenticate_user,
    create_access_token,
    get_current_admin,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@router.post("/login", response_model=Token)
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 password flow — returns a JWT access token."""
    pool = request.app.state.pool
    user = await authenticate_user(pool, form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user["username"])
    return Token(access_token=token)


@router.get("/me", response_model=AdminUser)
async def get_me(request: Request, current: TokenData = Depends(get_current_admin)):
    """Return the currently logged-in admin user."""
    pool = request.app.state.pool
    async with pool.connection() as conn:
        cur = await conn.execute(
            "SELECT id, username, full_name, is_active FROM admin_users WHERE username = %s",
            (current.username,),
        )
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return AdminUser(id=row[0], username=row[1], full_name=row[2], is_active=row[3])


# ---------------------------------------------------------------------------
# Analytics endpoints
# ---------------------------------------------------------------------------

@router.get("/analytics/summary")
async def analytics_summary(request: Request, _: TokenData = Depends(get_current_admin)):
    """Dashboard summary: total chats, today's chats, pending questions, total questions."""
    pool = request.app.state.pool
    async with pool.connection() as conn:
        # Total unique threads (from checkpoints)
        cur = await conn.execute("SELECT COUNT(DISTINCT thread_id) FROM checkpoints")
        total_threads = (await cur.fetchone())[0]

        # Today's chats
        cur = await conn.execute(
            "SELECT COUNT(*) FROM chat_analytics WHERE created_at >= CURRENT_DATE"
        )
        today_chats = (await cur.fetchone())[0]

        # Total chat messages tracked
        cur = await conn.execute("SELECT COUNT(*) FROM chat_analytics")
        total_messages = (await cur.fetchone())[0]

        # Unanswered questions
        cur = await conn.execute(
            "SELECT COUNT(*) FROM unanswered_questions WHERE status = 'pending'"
        )
        pending_questions = (await cur.fetchone())[0]

        cur = await conn.execute("SELECT COUNT(*) FROM unanswered_questions")
        total_questions = (await cur.fetchone())[0]

    return {
        "total_threads": total_threads,
        "today_chats": today_chats,
        "total_messages": total_messages,
        "pending_questions": pending_questions,
        "total_questions": total_questions,
    }


@router.get("/analytics/daily")
async def analytics_daily(request: Request, days: int = 7, _: TokenData = Depends(get_current_admin)):
    """Chat count per day for the last N days."""
    pool = request.app.state.pool
    async with pool.connection() as conn:
        cur = await conn.execute(
            """
            SELECT created_at::date AS day, COUNT(*) AS count
            FROM chat_analytics
            WHERE created_at >= CURRENT_DATE - %s * INTERVAL '1 day'
            GROUP BY day
            ORDER BY day
            """,
            (days,),
        )
        rows = await cur.fetchall()
    return {"daily": [{"date": str(r[0]), "count": r[1]} for r in rows]}


# ---------------------------------------------------------------------------
# Unanswered questions CRUD
# ---------------------------------------------------------------------------

class AnswerRequest(BaseModel):
    answer: str


@router.get("/questions")
async def list_questions(
    request: Request,
    status_filter: str = "pending",
    _: TokenData = Depends(get_current_admin),
):
    """List unanswered questions, filterable by status."""
    pool = request.app.state.pool
    async with pool.connection() as conn:
        if status_filter == "all":
            cur = await conn.execute(
                "SELECT id, question, language, thread_id, status, admin_answer, created_at, answered_at "
                "FROM unanswered_questions ORDER BY created_at DESC LIMIT 100"
            )
        else:
            cur = await conn.execute(
                "SELECT id, question, language, thread_id, status, admin_answer, created_at, answered_at "
                "FROM unanswered_questions WHERE status = %s ORDER BY created_at DESC LIMIT 100",
                (status_filter,),
            )
        rows = await cur.fetchall()

    return {
        "questions": [
            {
                "id": r[0],
                "question": r[1],
                "language": r[2],
                "thread_id": r[3],
                "status": r[4],
                "admin_answer": r[5],
                "created_at": str(r[6]) if r[6] else None,
                "answered_at": str(r[7]) if r[7] else None,
            }
            for r in rows
        ]
    }


@router.get("/conversations")
async def list_conversations(request: Request, _: TokenData = Depends(get_current_admin)):
    """List all unique thread IDs and their latest activity from checkpoints."""
    pool = request.app.state.pool
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            # LangGraph checkpoints table usually has a 'checkpoint' JSONB column 
            # or we can look at the latest row for each thread.
            # Assuming checkpoints table structure from psycopg checkpointer.
            await cur.execute("""
                SELECT thread_id, MAX(checkpoint_id) as last_id
                FROM checkpoints
                GROUP BY thread_id
                ORDER BY last_id DESC
                LIMIT 100
            """)
            rows = await cur.fetchall()
            
    return {"threads": [{"id": row[0], "last_activity": row[1]} for row in rows]}


@router.put("/questions/{question_id}/answer")
async def answer_question(
    question_id: int,
    body: AnswerRequest,
    request: Request,
    _: TokenData = Depends(get_current_admin),
):
    """Admin provides an answer to a flagged question."""
    pool = request.app.state.pool
    async with pool.connection() as conn:
        cur = await conn.execute(
            """
            UPDATE unanswered_questions
            SET admin_answer = %s, status = 'answered', answered_at = %s
            WHERE id = %s
            RETURNING id
            """,
            (body.answer, datetime.now(timezone.utc), question_id),
        )
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"ok": True, "id": row[0]}


@router.put("/questions/{question_id}/dismiss")
async def dismiss_question(
    question_id: int,
    request: Request,
    _: TokenData = Depends(get_current_admin),
):
    """Dismiss a question (not relevant / duplicate)."""
    pool = request.app.state.pool
    async with pool.connection() as conn:
        cur = await conn.execute(
            "UPDATE unanswered_questions SET status = 'dismissed' WHERE id = %s RETURNING id",
            (question_id,),
        )
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"ok": True, "id": row[0]}


# ---------------------------------------------------------------------------
# Knowledge base management
# ---------------------------------------------------------------------------

@router.get("/knowledge/status")
async def knowledge_status(
    request: Request,
    _: TokenData = Depends(get_current_admin),
):
    """Return the current state of the vector knowledge base."""
    from agent.tools.knowledge_base import count_chunks
    pool = request.app.state.pool

    total = await count_chunks()

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT source_type, COUNT(*) as chunks, COUNT(DISTINCT source_url) as urls
                FROM knowledge_chunks
                GROUP BY source_type
                ORDER BY source_type
                """
            )
            rows = await cur.fetchall()
            breakdown = [
                {"type": r[0], "chunks": r[1], "urls": r[2]}
                for r in rows
            ]

            await cur.execute(
                """
                SELECT source_url, source_type, COUNT(*) as chunks,
                       MAX(indexed_at) as last_indexed
                FROM knowledge_chunks
                GROUP BY source_url, source_type
                ORDER BY last_indexed DESC
                LIMIT 60
                """
            )
            urls = await cur.fetchall()
            indexed_urls = [
                {"url": r[0], "type": r[1], "chunks": r[2],
                 "indexed_at": r[3].isoformat() if r[3] else None}
                for r in urls
            ]

    return {
        "total_chunks": total,
        "breakdown": breakdown,
        "indexed_urls": indexed_urls,
    }


@router.post("/knowledge/reindex")
async def knowledge_reindex(
    request: Request,
    _: TokenData = Depends(get_current_admin),
):
    """
    Wipe and fully re-crawl all KEY_PAGES and KNOWN_PDFS.
    Runs in the background — returns immediately.
    Check /knowledge/status to monitor progress.
    """
    import asyncio
    from agent.tools.indexer import force_reindex
    from agent.tools.knowledge_base import set_pool

    pool = request.app.state.pool
    set_pool(pool)

    async def _run():
        try:
            result = await force_reindex()
            logger.info("Manual reindex complete: %s", result)
        except Exception:
            logger.exception("Manual reindex failed")

    asyncio.create_task(_run())
    return {"ok": True, "message": "Re-indexing started in background. Check /knowledge/status for progress."}
