"""
PDF extraction tool — fetches, parses, chunks and caches PDFs from *.yu.edu.jo.
Works alongside web_page_tool: that tool discovers PDF URLs, this one reads them.
"""
from __future__ import annotations
import asyncio
import hashlib
import io
import logging
from urllib.parse import urlparse

import aiohttp
import PyPDF2
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=120,
    separators=["\n\n", "\n", " ", ""],
)

_pdf_cache: dict[str, dict] = {}


def _allowed(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host.endswith(".yu.edu.jo") or host in ("yu.edu.jo", "www.yu.edu.jo")


async def _fetch_bytes(url: str, timeout: float = 20.0) -> bytes:
    if not url.startswith("http"):
        url = "https://admreg.yu.edu.jo" + ("" if url.startswith("/") else "/") + url
    if not _allowed(url):
        raise ValueError(f"Domain not allowed: {urlparse(url).netloc}")
    hdrs = {"User-Agent": "YarmoukAI/1.0"}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, timeout=aiohttp.ClientTimeout(total=timeout),
                         headers=hdrs, allow_redirects=True) as r:
            if r.status != 200:
                raise ValueError(f"HTTP {r.status} for {url}")
            return await r.read()


def _extract(pdf_bytes: bytes) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    pages = []
    for i, page in enumerate(reader.pages, 1):
        try:
            t = page.extract_text() or ""
            if t.strip():
                pages.append(f"[Page {i}]\n{t}")
            else:
                pages.append(f"[Page {i} — no text layer]")
        except Exception:
            pages.append(f"[Page {i} — unreadable]")
    return "\n\n".join(pages)


async def _process(url: str) -> dict:
    key = hashlib.md5(url.encode()).hexdigest()
    if key in _pdf_cache:
        logger.info("PDF cache hit: %s", url)
        return _pdf_cache[key]
    raw = await _fetch_bytes(url)
    logger.info("Extracting PDF (%d bytes): %s", len(raw), url)
    full_text = _extract(raw)
    chunks = _splitter.split_text(full_text)
    result = {"url": url, "text": full_text, "chunks": chunks,
              "pages": full_text.count("[Page ")}
    _pdf_cache[key] = result
    logger.info("PDF done: %d pages, %d chunks", result["pages"], len(chunks))

    # Auto-index new PDF content into the vector knowledge base (fire-and-forget)
    try:
        from .knowledge_base import save_to_knowledge
        asyncio.create_task(save_to_knowledge(url, chunks, "pdf"))
    except Exception:
        pass

    return result


@tool
async def pdf_extraction_tool(pdf_url: str, query: str = "") -> str:
    """
    Download and extract the full text from a PDF document on the Yarmouk University website.

    Use this tool whenever:
    - web_page_tool returns PDF links and you need to read what is inside them
    - A user asks about specific information that is typically in a document:
        • Academic calendars and semester dates (admreg.yu.edu.jo)
        • Majors list and program plans
        • University laws and regulations (law.yu.edu.jo)
        • Admission procedures and requirements
        • Staff phone directories
        • Financial rules and fee schedules
        • Training programs and professional diplomas (qrc.yu.edu.jo)
        • Accreditation reports (aqac.yu.edu.jo)

    Args:
        pdf_url: Full URL to the PDF. Must be on *.yu.edu.jo.
                 Example: https://admreg.yu.edu.jo/images/docs/majors.pdf
        query:   Keywords to find relevant sections in the document.
                 Leave empty to get an overview of the first few pages.

    Returns:
        Extracted text — either keyword-filtered chunks or an overview
    """
    try:
        data = await _process(pdf_url)
        chunks = data["chunks"]
        pages  = data["pages"]

        if query:
            words = query.lower().split()
            matched = [c for c in chunks if any(w in c.lower() for w in words)]
            if matched:
                body = "\n\n---\n\n".join(matched[:6])
                note = f"\n\n*(Showing {len(matched)}/{len(chunks)} chunks matching \"{query}\")*"
            else:
                body = "\n\n---\n\n".join(chunks[:3])
                note = f"\n\n*(No chunks matched \"{query}\" — showing first 3 chunks)*"
        else:
            body = "\n\n---\n\n".join(chunks[:3])
            note = f"\n\n*(Showing 3 of {len(chunks)} chunks from {pages}-page PDF. Add query= to filter.)*"

        return f"📄 **PDF**: {pdf_url}\n**Pages**: {pages} | **Chunks**: {len(chunks)}\n\n{body}{note}"

    except ValueError as e:
        return f"⚠️ {e}"
    except Exception as e:
        logger.exception("pdf_extraction_tool error: %s", pdf_url)
        return f"❌ Failed to process PDF: {e}"


def clear_pdf_cache():
    _pdf_cache.clear()
