"""
Ingest service: fetch + clean web pages.

Security hardening:
  - SSRF: resolved host IP is validated against private/loopback ranges before request.
  - Size: Content-Length header enforced; streaming body capped at MAX_HTML_BYTES.
  - Timeout: 15 s hard limit.
  - Duplicate prevention: one record per (user_id, url).
"""
import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from sqlmodel import Session, select

from app.models.document import Document

# Hard cap on raw HTML stored / fetched (5 MB)
MAX_HTML_BYTES = 5 * 1024 * 1024  # 5 MB
# Hard cap on cleaned text stored in DB (500 KB)
MAX_CLEANED_BYTES = 500 * 1024  # 500 KB

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


def _assert_safe_url(url: str) -> None:
    """Raise ValueError if the URL resolves to a private/internal IP (SSRF guard)."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid URL: no hostname found.")

    # Block raw IP literals that look private before DNS resolution
    try:
        addr = ipaddress.ip_address(hostname)
        for net in _PRIVATE_NETWORKS:
            if addr in net:
                raise ValueError(f"Requests to private/internal addresses are not allowed.")
    except ValueError as e:
        # ip_address() raises ValueError for hostnames — only re-raise if it's our rejection
        if "not allowed" in str(e):
            raise

    # DNS resolution + check
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise ValueError(f"Could not resolve hostname: {hostname}")

    for info in infos:
        raw_ip = info[4][0]
        try:
            addr = ipaddress.ip_address(raw_ip)
        except ValueError:
            continue
        for net in _PRIVATE_NETWORKS:
            if addr in net:
                raise ValueError("Requests to private/internal addresses are not allowed.")


async def fetch_and_clean_url(url: str, user_id: int, session: Session) -> Document:
    # 1. SSRF guard
    _assert_safe_url(url)

    # 2. Duplicate prevention — return existing record if already ingested for this user
    existing_stmt = select(Document).where(
        Document.user_id == user_id,
        Document.url == url,
    )
    existing = session.exec(existing_stmt).first()
    if existing:
        return existing

    # 3. Fetch with size enforcement
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
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
    soup = BeautifulSoup(raw_html, "html.parser")
    title = soup.title.string if soup.title and soup.title.string else url

    for element in soup(
        ["script", "style", "meta", "noscript", "header", "footer", "nav", "aside", "svg"]
    ):
        element.extract()

    cleaned_content = soup.get_text(separator="\n", strip=True)

    # Trim stored content to avoid unbounded DB growth
    raw_to_store = raw_html[:MAX_HTML_BYTES]
    cleaned_to_store = cleaned_content[:MAX_CLEANED_BYTES]

    doc = Document(
        user_id=user_id,
        url=url,
        title=title.strip()[:200],
        raw_content=raw_to_store,
        cleaned_content=cleaned_to_store,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc
