"""
Shared knowledge base for Yarmouk University AI assistant.
All scraped content is embedded and stored here.
The RAG tool searches here FIRST before any live web calls.
"""
from __future__ import annotations
import asyncio
import logging
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# ── globals (set at app startup) ──────────────────────────────────────────────
_pool: Any = None
_openai = AsyncOpenAI()

EMBED_MODEL = "text-embedding-3-small"
DIMS = 1536
MIN_SCORE = 0.28   # cosine similarity threshold (~0.28 = loosely relevant)

# Reusable splitter for page text (PDFs are already chunked by pdf_extractor)
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800, chunk_overlap=100,
    separators=["\n\n", "\n", " ", ""],
)


def set_pool(pool: Any) -> None:
    """Inject the async DB pool at startup — must be called before any searches."""
    global _pool
    _pool = pool
    logger.info("Knowledge base: DB pool attached")


def chunk_text(text: str) -> list[str]:
    """Split raw page text into indexable chunks."""
    return _splitter.split_text(text)


# ── embedding ─────────────────────────────────────────────────────────────────

async def _embed(text: str) -> list[float]:
    resp = await _openai.embeddings.create(model=EMBED_MODEL, input=text[:8000])
    return resp.data[0].embedding


def _vec_str(vec: list[float]) -> str:
    """Format a float list as a pgvector literal: [0.1,0.2,...]"""
    return "[" + ",".join(str(x) for x in vec) + "]"


# ── search ────────────────────────────────────────────────────────────────────

async def search_knowledge(query: str, k: int = 6) -> list[dict]:
    """
    Semantic search over all indexed chunks.
    Returns up to k results above MIN_SCORE, sorted by relevance.
    """
    if _pool is None:
        logger.warning("search_knowledge called before pool set")
        return []
    try:
        vec = await _embed(query)
        vs = _vec_str(vec)
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT source_url, source_type, content,
                           1 - (embedding <=> %s::vector) AS score
                    FROM knowledge_chunks
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (vs, vs, k),
                )
                rows = await cur.fetchall()
        results = [
            {"url": r[0], "type": r[1], "content": r[2], "score": float(r[3])}
            for r in rows
            if float(r[3]) >= MIN_SCORE
        ]
        logger.info("search_knowledge: %d/%d chunks above threshold for %r",
                    len(results), len(rows), query[:60])
        return results
    except Exception:
        logger.exception("search_knowledge failed")
        return []


# ── save ──────────────────────────────────────────────────────────────────────

async def save_to_knowledge(url: str, chunks: list[str], source_type: str = "page") -> int:
    """
    Embed and store chunks for a URL. Idempotent — skips URLs already indexed.
    Returns number of new chunks saved (0 if already indexed).
    """
    if _pool is None or not chunks:
        return 0
    # Clean chunks first (outside any DB connection)
    clean_chunks = [c for c in chunks if c.strip()]
    if not clean_chunks:
        return 0
    try:
        # 1) Quick existence check — acquire + release connection immediately
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT COUNT(*) FROM knowledge_chunks WHERE source_url = %s", (url,)
                )
                row = await cur.fetchone()
                if row and int(row[0]) > 0:
                    logger.debug("Already indexed (%d chunks): %s", row[0], url)
                    return 0

        # 2) Embed ALL chunks BEFORE opening a DB connection — prevents
        #    "another command is already in progress" caused by awaiting
        #    the OpenAI API while a psycopg cursor is held open.
        vecs = [await _embed(c) for c in clean_chunks]

        # 3) Re-open connection for inserts (re-check in case concurrent task indexed it)
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT COUNT(*) FROM knowledge_chunks WHERE source_url = %s", (url,)
                )
                row = await cur.fetchone()
                if row and int(row[0]) > 0:
                    logger.debug("Already indexed (%d chunks): %s", row[0], url)
                    return 0

                count = 0
                for chunk, vec in zip(clean_chunks, vecs):
                    await cur.execute(
                        """
                        INSERT INTO knowledge_chunks
                            (source_url, source_type, content, embedding)
                        VALUES (%s, %s, %s, %s::vector)
                        """,
                        (url, source_type, chunk, _vec_str(vec)),
                    )
                    count += 1

        logger.info("Indexed %d new chunks: %s (%s)", count, url, source_type)
        return count
    except Exception:
        logger.exception("save_to_knowledge failed for %s", url)
        return 0


# ── helpers ───────────────────────────────────────────────────────────────────

async def count_chunks() -> int:
    """Return total number of indexed chunks in the knowledge base."""
    if _pool is None:
        return 0
    try:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) FROM knowledge_chunks")
                row = await cur.fetchone()
                return int(row[0]) if row else 0
    except Exception:
        return 0


async def is_indexed(url: str) -> bool:
    """Check whether a URL has already been indexed."""
    if _pool is None:
        return False
    try:
        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT 1 FROM knowledge_chunks WHERE source_url = %s LIMIT 1", (url,)
                )
                return bool(await cur.fetchone())
    except Exception:
        return False
