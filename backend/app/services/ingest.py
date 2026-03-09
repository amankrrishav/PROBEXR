"""
Ingest service: fetch + clean web pages and save text documents.

Security hardening:
  - SSRF: resolved host IP is validated against private/loopback ranges before request.
  - Size: Content-Length header enforced; streaming body capped at MAX_HTML_BYTES.
  - Timeout: 15 s hard limit.
  - Duplicate prevention: one record per (user_id, url).
  - DNS: resolution is non-blocking via run_in_executor.
"""
import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.document import Document

# Hard cap on raw HTML stored / fetched (5 MB)
MAX_HTML_BYTES = 5 * 1024 * 1024  # 5 MB
# Hard cap on cleaned text stored in DB (500 KB)
MAX_CLEANED_BYTES = 500 * 1024  # 500 KB
# Hard cap on text ingest (500 KB)
MAX_TEXT_BYTES = 500 * 1024  # 500 KB

_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local
    ipaddress.ip_network("0.0.0.0/8"),
]


def _check_ip_not_private(addr_str: str) -> None:
    """Raise ValueError if an IP address is in a private/internal range."""
    try:
        addr = ipaddress.ip_address(addr_str)
    except ValueError:
        return
    for net in _PRIVATE_NETWORKS:
        if addr in net:
            raise ValueError("Requests to private/internal addresses are not allowed.")


async def _assert_safe_url(url: str) -> None:
    """Raise ValueError if the URL resolves to a private/internal IP (SSRF guard).
    DNS resolution is offloaded to a thread pool to avoid blocking the event loop.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid URL: no hostname found.")

    # Block raw IP literals that look private before DNS resolution
    try:
        addr = ipaddress.ip_address(hostname)
        _check_ip_not_private(str(addr))
    except ValueError as e:
        if "not allowed" in str(e):
            raise

    # DNS resolution in executor (non-blocking)
    loop = asyncio.get_event_loop()
    try:
        infos = await loop.run_in_executor(None, socket.getaddrinfo, hostname, None)
    except socket.gaierror:
        raise ValueError(f"Could not resolve hostname: {hostname}")

    for info in infos:
        raw_ip: str = str(info[4][0])
        _check_ip_not_private(raw_ip)


async def fetch_and_clean_url(url: str, user_id: int, session: AsyncSession) -> Document:
    # 1. SSRF guard (async-safe)
    await _assert_safe_url(url)

    # 2. Duplicate prevention — return existing record if already ingested for this user
    existing_stmt = select(Document).where(
        Document.user_id == user_id,
        Document.url == url,
    )
    fake_url = f"https://storage.probefy.local/audio/{uuid.uuid4()}.mp3"
    result = await session.execute(existing_stmt)
    existing = result.scalars().first()
    if existing:
        return existing

    # 3. Fetch with size enforcement
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; PROBEfy/1.0; +http://localhost)"
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, headers=headers) as client:
        # Start a streaming request to read Content-Length header first
        async with client.stream("GET", url) as response:
            response.raise_for_status()

            # Content-Length pre-check
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > MAX_HTML_BYTES:
                raise ValueError(
                    f"Page too large ({int(content_length) // 1024} KB). Max allowed: {MAX_HTML_BYTES // 1024} KB."
                )

            # Stream body with hard byte cap
            chunks: list[bytes] = []
            total = 0
            async for chunk in response.aiter_bytes(chunk_size=65536):
                total += len(chunk)
                if total > MAX_HTML_BYTES:
                    raise ValueError(
                        f"Page too large (>{MAX_HTML_BYTES // 1024} KB). Max allowed: {MAX_HTML_BYTES // 1024} KB."
                    )
                chunks.append(chunk)

    raw_bytes = b"".join(chunks)
    # Decode, lenient
    raw_html = raw_bytes.decode("utf-8", errors="replace")

    # 4. Parse + clean
    import re
    soup = BeautifulSoup(raw_html, "html.parser")
    title = soup.title.string if soup.title and soup.title.string else url

    # Remove noisy tags
    for element in soup(
        ["script", "style", "meta", "noscript", "header", "footer", "nav", "aside", "svg"]
    ):
        element.extract()

    # Remove noisy elements by id or class (Wikipedia chrome, generic site UI)
    NOISY_IDS = {
        "catlinks", "mw-navigation", "mw-head", "mw-panel", "mw-page-base",
        "mw-head-base", "footer", "siteNotice", "contentSub", "jump-to-nav",
        "mw-fr-toolbar", "toc",
    }
    NOISY_CLASSES = {
        "navbox", "navbox-inner", "navbox-group", "navbox-list",
        "reflist", "refbegin", "references",
        "mw-editsection", "mw-jump-link", "mw-indicators",
        "printfooter", "catlinks", "sistersitebox",
        "infobox", "sidebar", "toc", "thumb", "noprint",
        "hatnote", "mbox", "ambox", "ombox", "tmbox", "fmbox", "cmbox",
        "spoken-wikipedia", "bandeau-container",
    }
    for element in soup.find_all(True):
        el_id = element.get("id", "")
        classes_raw = element.get("class")
        if not classes_raw:
            el_classes = set()
        elif isinstance(classes_raw, list):
            el_classes = set(classes_raw)
        else:
            el_classes = set([str(classes_raw)])
        if el_id in NOISY_IDS or bool(el_classes & NOISY_CLASSES):
            element.extract()

    cleaned_content = soup.get_text(separator="\n", strip=True)

    # Collapse excessive blank lines
    cleaned_content = re.sub(r"\n{3,}", "\n\n", cleaned_content).strip()

    # Trim stored content to avoid unbounded DB growth
    cleaned_to_store = cleaned_content[:MAX_CLEANED_BYTES]

    doc = Document(
        user_id=user_id,
        url=url,
        title=title.strip()[:200],
        cleaned_content=cleaned_to_store,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return doc


async def ingest_text_document(user_id: int, text: str, title: str, session: AsyncSession) -> Document:
    """Save a pasted text document. Extracted from router to maintain service layer separation."""
    # Auto-generate title from content when the caller passes a generic placeholder
    if not title or title.strip().lower() in ("pasted text", "untitled", ""):
        words = text.strip().split()[:12]
        title = " ".join(words)
        if len(title) > 80:
            title = title[:77] + "…"
        if not title:
            title = "Untitled Note"
    doc = Document(
        user_id=user_id,
        url="pasted_text",
        title=title[:200],
        cleaned_content=text[:MAX_TEXT_BYTES],
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return doc
