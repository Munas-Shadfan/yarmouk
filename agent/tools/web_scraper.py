"""
Universal web scraper for the entire Yarmouk University ecosystem.
Covers www.yu.edu.jo and ALL subdomains: admreg, library, qrc, aqac, etc.
Extracts clean text AND discovers all PDF links on each page.
"""
from __future__ import annotations
import asyncio
import hashlib
import logging
import re
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Every known *.yu.edu.jo origin — any new subdomain also auto-passes the wildcard check below
ALLOWED_DOMAINS: set[str] = {
    "yu.edu.jo", "www.yu.edu.jo",
    "admreg.yu.edu.jo",   # Admission & Registration — KEY: calendars, PDFs, deadlines
    "sis.yu.edu.jo",       # Student Information System
    "elearning.yu.edu.jo", # eLearning platform
    "library.yu.edu.jo",   # Hussein bin Talal Library
    "qrc.yu.edu.jo",       # Queen Rania Center for Jordanian Studies
    "aqac.yu.edu.jo",      # Accreditation & Quality Assurance Center
    "hr.yu.edu.jo",        # Human Resources — jobs, scholarships
    "fmd.yu.edu.jo",       # Faculty Members Directory
    "daleel.yu.edu.jo",    # Staff phone directory
    "law.yu.edu.jo",       # University laws & regulations
    "elc.yu.edu.jo",       # English Language Center
    "apsol.yu.edu.jo",     # Arabic for non-native speakers
    "alumni.yu.edu.jo",    # Alumni network
    "mowazi.yu.edu.jo",    # Student tracker / Muwazi
    "qubul.yu.edu.jo",     # Admissions portal
    "mschool.yu.edu.jo",   # Model school
    "yufm.yu.edu.jo",      # University radio
    "tendering.yu.edu.jo", # Tenders
}

_page_cache: dict[str, dict] = {}

# HTML tags that contain zero useful text
_STRIP_TAGS = {"script", "style", "noscript", "form",
               "button", "input", "meta", "link", "img", "svg", "canvas"}


def _is_allowed(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host in ALLOWED_DOMAINS or host.endswith(".yu.edu.jo")


def _pdf_links_on_page(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Return all .pdf hrefs resolved to absolute URLs, filtered to *.yu.edu.jo."""
    seen, out = set(), []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().endswith(".pdf"):
            abs_url = urljoin(base_url, href)
            if _is_allowed(abs_url) and abs_url not in seen:
                seen.add(abs_url)
                out.append(abs_url)
    return out


def _clean_html(soup: BeautifulSoup) -> str:
    for tag in soup(list(_STRIP_TAGS)):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


async def _fetch(url: str, timeout: float = 14.0) -> dict:
    key = hashlib.md5(url.encode()).hexdigest()
    if key in _page_cache:
        return _page_cache[key]
    if not _is_allowed(url):
        raise ValueError(f"Domain not allowed: {urlparse(url).netloc} — only *.yu.edu.jo")
    hdrs = {"User-Agent": "YarmoukAI/1.0 (university assistant bot)"}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, timeout=aiohttp.ClientTimeout(total=timeout),
                         headers=hdrs, allow_redirects=True) as r:
            if r.status != 200:
                raise ValueError(f"HTTP {r.status} fetching {url}")
            html = await r.text(errors="replace")
    soup = BeautifulSoup(html, "lxml")
    title = (soup.title.string or "").strip() if soup.title else ""
    text  = _clean_html(soup)
    pdfs  = _pdf_links_on_page(soup, url)
    result = {"url": url, "title": title, "text": text, "pdf_links": pdfs}
    _page_cache[key] = result
    logger.info("Scraped %d chars + %d PDFs: %s", len(text), len(pdfs), url)

    # Auto-index new content into the vector knowledge base (fire-and-forget)
    try:
        from .knowledge_base import save_to_knowledge, chunk_text
        asyncio.create_task(save_to_knowledge(url, chunk_text(text), "page"))
    except Exception:
        pass

    return result


@tool
async def web_page_tool(url: str, query: str = "") -> str:
    """
    Scrape ANY page on the Yarmouk University website or its subdomains and extract its content.

    Covers ALL of:
      • www.yu.edu.jo           — main university site (news, announcements, info)
      • admreg.yu.edu.jo        — Admission & Registration (calendars, deadlines, procedures)
      • library.yu.edu.jo       — Hussein bin Talal Library (resources, databases)
      • qrc.yu.edu.jo           — Queen Rania Center (training, diplomas, courses)
      • aqac.yu.edu.jo          — Accreditation & Quality Assurance
      • hr.yu.edu.jo            — Human Resources (jobs, scholarships)
      • fmd.yu.edu.jo           — Faculty directory
      • daleel.yu.edu.jo        — Staff phone directory
      • law.yu.edu.jo           — University laws and regulations
      • elc.yu.edu.jo           — English Language Center
      • alumni.yu.edu.jo        — Alumni network
      • mowazi.yu.edu.jo        — Student academic tracker
      • qubul.yu.edu.jo         — Admissions portal

    IMPORTANT: This tool also returns a list of PDF links found on the page.
    After calling this, call pdf_extraction_tool on any relevant PDFs to get full document content.

    Args:
        url:   Full URL of the page to scrape (must be *.yu.edu.jo)
        query: Optional keywords to filter text to relevant lines only

    Returns:
        Clean page text + list of discovered PDF links
    """
    try:
        data = await _fetch(url)
        text = data["text"]
        pdfs = data["pdf_links"]
        title = data["title"]

        if query:
            words = query.lower().split()
            lines = text.split("\n")
            relevant = [l for l in lines if any(w in l.lower() for w in words)]
            body = "\n".join(relevant[:100]) if relevant else text[:2500]
            note = f"\n\n*(Showing {len(relevant)} lines matching \"{query}\")*"
        else:
            body = text[:3500]
            note = ("\n\n*(Large page — pass a query= to filter)*" if len(text) > 3500 else "")

        out = f"🌐 **{title or url}**\n**URL**: {url}\n\n{body}{note}"
        if pdfs:
            out += f"\n\n📎 **{len(pdfs)} PDF(s) found on this page:**\n"
            out += "\n".join(f"  • {p}" for p in pdfs)
        return out

    except ValueError as e:
        return f"⚠️ {e}"
    except Exception as e:
        logger.exception("web_page_tool error: %s", url)
        return f"❌ Could not scrape page: {e}"


def clear_page_cache():
    _page_cache.clear()
