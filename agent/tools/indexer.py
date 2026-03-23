"""
Startup indexer — crawls all KEY_PAGES and KNOWN_PDFS into the vector knowledge base.
Run once at app startup (idempotent); any subsequent scraping auto-updates the DB.
"""
from __future__ import annotations
import asyncio
import logging

from .knowledge_base import count_chunks, save_to_knowledge, chunk_text
from .pdf_helpers import KEY_PAGES, KNOWN_PDFS

logger = logging.getLogger(__name__)


async def _index_page(url: str) -> int:
    try:
        from .web_scraper import _fetch
        data = await _fetch(url)
        chunks = chunk_text(data["text"])
        return await save_to_knowledge(url, chunks, "page")
    except Exception as e:
        logger.warning("index_page failed %s: %s", url, e)
        return 0


async def _index_pdf(url: str) -> int:
    try:
        from .pdf_extractor import _process
        data = await _process(url)
        return await save_to_knowledge(url, data["chunks"], "pdf")
    except Exception as e:
        logger.warning("index_pdf failed %s: %s", url, e)
        return 0


async def run_initial_indexing(force: bool = False) -> dict:
    """
    Crawl all KEY_PAGES and KNOWN_PDFS and store them in the vector knowledge base.
    Skips URLs already indexed (idempotent) unless force=True.
    Designed to run in the background at app startup.
    """
    existing = await count_chunks()
    if existing > 0 and not force:
        logger.info("Knowledge base already has %d chunks — skipping initial indexing", existing)
        return {"status": "skipped", "existing_chunks": existing}

    page_urls = [info["url"] for info in KEY_PAGES.values()]
    pdf_urls  = [info["url"] for info in KNOWN_PDFS.values()]
    logger.info("Starting initial indexing: %d pages + %d PDFs", len(page_urls), len(pdf_urls))

    # Pages — up to 3 concurrent fetches
    sem = asyncio.Semaphore(3)

    async def _guarded_page(url: str) -> int:
        async with sem:
            result = await _index_page(url)
            await asyncio.sleep(0.3)   # polite crawl delay
            return result

    page_results = await asyncio.gather(
        *[_guarded_page(u) for u in page_urls], return_exceptions=True
    )
    page_chunks = sum(r for r in page_results if isinstance(r, int))

    # PDFs — sequential (larger files)
    pdf_chunks = 0
    for url in pdf_urls:
        pdf_chunks += await _index_pdf(url)
        await asyncio.sleep(0.5)

    total = await count_chunks()
    logger.info(
        "Initial indexing done: %d page + %d PDF chunks → %d total in DB",
        page_chunks, pdf_chunks, total,
    )
    return {
        "status": "complete",
        "page_chunks": page_chunks,
        "pdf_chunks": pdf_chunks,
        "total_chunks": total,
    }

async def force_reindex() -> dict:
    """
    Wipe the entire knowledge base and re-crawl every KEY_PAGE and KNOWN_PDF.
    Use this when the website content changes or after adding new URLs to pdf_helpers.py.
    """
    from .knowledge_base import _pool
    if _pool is None:
        return {"status": "error", "detail": "DB pool not attached"}

    logger.info("Force re-index: wiping knowledge_chunks table...")
    async with _pool.connection() as conn:
        await conn.execute("DELETE FROM knowledge_chunks")
    logger.info("knowledge_chunks cleared — starting full re-crawl")

    # Clear in-memory caches so fresh content is fetched
    from .web_scraper import clear_page_cache
    from .pdf_extractor import clear_pdf_cache
    clear_page_cache()
    clear_pdf_cache()

    return await run_initial_indexing(force=True)