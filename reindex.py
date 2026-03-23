"""
Standalone reindex script — wipes knowledge_chunks and re-crawls everything.
Run with:  python reindex.py
"""
from __future__ import annotations
import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("reindex")

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    print("❌  DATABASE_URL not set in .env")
    sys.exit(1)


async def main():
    from psycopg_pool import AsyncConnectionPool
    from agent.tools.knowledge_base import set_pool, count_chunks
    from agent.tools.pdf_helpers import KEY_PAGES, KNOWN_PDFS

    pool = AsyncConnectionPool(
        conninfo=DATABASE_URL,
        min_size=1,
        max_size=5,
        open=False,
        kwargs={"autocommit": True},
    )
    await pool.open(wait=True, timeout=30)
    set_pool(pool)
    logger.info("DB pool ready")

    # ── 1. Show current state ────────────────────────────────────────────────
    before = await count_chunks()
    logger.info("Current knowledge_chunks: %d rows", before)

    # ── 2. Wipe ──────────────────────────────────────────────────────────────
    async with pool.connection() as conn:
        await conn.execute("DELETE FROM knowledge_chunks")
    logger.info("Wiped all existing chunks")

    # Clear in-memory caches
    from agent.tools.web_scraper import clear_page_cache
    from agent.tools.pdf_extractor import clear_pdf_cache
    clear_page_cache()
    clear_pdf_cache()

    # ── 3. Index pages ───────────────────────────────────────────────────────
    from agent.tools.knowledge_base import save_to_knowledge, chunk_text
    from agent.tools.web_scraper import _fetch
    from agent.tools.pdf_extractor import _process

    page_urls = [info["url"] for info in KEY_PAGES.values()]
    pdf_urls  = [info["url"] for info in KNOWN_PDFS.values()]

    logger.info("Indexing %d pages + %d PDFs...", len(page_urls), len(pdf_urls))

    sem = asyncio.Semaphore(3)
    page_total = 0

    async def index_page(url: str) -> int:
        async with sem:
            try:
                data = await _fetch(url)
                chunks = chunk_text(data["text"])
                saved = await save_to_knowledge(url, chunks, "page")
                logger.info("  📄 page  +%d chunks  %s", saved, url)
                await asyncio.sleep(0.3)
                return saved
            except Exception as e:
                logger.warning("  ⚠️  page SKIP  %s  → %s", url, e)
                return 0

    results = await asyncio.gather(*[index_page(u) for u in page_urls])
    page_total = sum(results)

    # PDFs — sequential (large files)
    pdf_total = 0
    for url in pdf_urls:
        try:
            data = await _process(url)
            saved = await save_to_knowledge(url, data["chunks"], "pdf")
            logger.info("  📑 pdf   +%d chunks  %s", saved, url)
            pdf_total += saved
        except Exception as e:
            logger.warning("  ⚠️  pdf  SKIP  %s  → %s", url, e)
        await asyncio.sleep(0.5)

    # ── 4. Summary ───────────────────────────────────────────────────────────
    total = await count_chunks()
    print("\n" + "=" * 60)
    print(f"  ✅  Reindex complete")
    print(f"      Pages  : {page_total} chunks from {len(page_urls)} URLs")
    print(f"      PDFs   : {pdf_total} chunks from {len(pdf_urls)} documents")
    print(f"      TOTAL  : {total} chunks now in knowledge_chunks")
    print("=" * 60 + "\n")

    await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
