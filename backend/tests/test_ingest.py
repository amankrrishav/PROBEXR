"""
Ingestion smoke tests — text ingest and URL validation.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ingest_text_success(client: AsyncClient, registered_user: dict):
    client.cookies.set("access_token", f"Bearer {registered_user['token']}")
    res = await client.post(
        "/ingest/text",
        json={
            "text": "This is a sample document for testing purposes. " * 10,
            "title": "Test Document",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Test Document"
    assert data["user_id"] is not None
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_ingest_text_unauthenticated(client: AsyncClient):
    res = await client.post(
        "/ingest/text",
        json={"text": "Some text here for testing.", "title": "No Auth"},
    )
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# A-38: Parametrized SSRF test across all private IP ranges
# ---------------------------------------------------------------------------
# Covers every blocked network in ingest.py's _BLOCKED_NETWORKS:
#   10.0.0.0/8       — RFC-1918 private
#   172.16.0.0/12    — RFC-1918 private
#   192.168.0.0/16   — RFC-1918 private
#   127.0.0.0/8      — loopback
#   ::1/128          — IPv6 loopback
#   fc00::/7         — IPv6 unique local
#   169.254.0.0/16   — link-local (AWS metadata endpoint lives here)
#   0.0.0.0/8        — "this" network

_SSRF_BLOCKED_URLS = [
    # IPv4 private ranges
    ("10.0.0.1",        "RFC-1918 class A private"),
    ("10.255.255.255",  "RFC-1918 class A edge"),
    ("172.16.0.1",      "RFC-1918 class B private"),
    ("172.31.255.255",  "RFC-1918 class B edge"),
    ("192.168.0.1",     "RFC-1918 class C private"),
    ("192.168.255.255", "RFC-1918 class C edge"),
    # Loopback
    ("127.0.0.1",       "IPv4 loopback"),
    ("127.0.0.2",       "IPv4 loopback range"),
    ("127.255.255.255", "IPv4 loopback edge"),
    # Link-local — AWS metadata endpoint
    ("169.254.169.254", "AWS metadata / link-local"),
    ("169.254.0.1",     "link-local range start"),
    # This-network
    ("0.0.0.0",         "this-network address"),
    # IPv6 loopback
    ("::1",             "IPv6 loopback"),
    # IPv6 unique local
    ("fc00::1",         "IPv6 unique local"),
    ("fdff:ffff:ffff:ffff:ffff:ffff:ffff:ffff", "IPv6 unique local edge"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("ip,label", _SSRF_BLOCKED_URLS)
async def test_ingest_url_private_ip_blocked(
    client: AsyncClient, registered_user: dict, ip: str, label: str
):
    """SSRF protection: all private/reserved IP ranges must be rejected (A-38)."""
    client.cookies.set("access_token", f"Bearer {registered_user['token']}")

    # IPv6 addresses need brackets in URLs
    host = f"[{ip}]" if ":" in ip else ip
    url = f"http://{host}/secret"

    res = await client.post("/ingest/url", json={"url": url})
    assert res.status_code == 400, (
        f"Expected 400 for {label} ({ip}), got {res.status_code}: {res.text}"
    )
    detail = res.json()["detail"].lower()
    assert "not allowed" in detail or "private" in detail, (
        f"Unexpected error message for {label} ({ip}): {detail}"
    )


@pytest.mark.asyncio
async def test_ingest_url_invalid_scheme(client: AsyncClient, registered_user: dict):
    client.cookies.set("access_token", f"Bearer {registered_user['token']}")
    res = await client.post(
        "/ingest/url",
        json={"url": "ftp://example.com/file"},
    )
    # Pydantic validation: must start with http:// or https://
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_ingest_url_unauthenticated(client: AsyncClient):
    res = await client.post(
        "/ingest/url",
        json={"url": "https://example.com"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_ingest_ssrf_redirect_to_metadata_blocked(authed_client: AsyncClient):
    """SSRF redirect bypass: a safe URL that 302-redirects to an internal IP must be rejected."""
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.services.ingest import _assert_safe_url as real_assert_safe_url

    # Build a fake 302 response pointing to the AWS metadata endpoint
    redirect_response = MagicMock()
    redirect_response.status_code = 302
    redirect_response.headers = {"location": "http://169.254.169.254/latest/meta-data/"}
    redirect_response.__aenter__ = AsyncMock(return_value=redirect_response)
    redirect_response.__aexit__ = AsyncMock(return_value=False)

    mock_client = MagicMock()
    mock_client.stream = MagicMock(return_value=redirect_response)

    # Allow the initial URL to pass SSRF check, but run real validation on redirects
    call_count = 0
    async def _selective_assert_safe_url(url: str) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return  # skip DNS check for fake initial domain
        await real_assert_safe_url(url)

    with patch("app.services.ingest.get_http_client", return_value=mock_client), \
         patch("app.services.ingest._assert_safe_url", side_effect=_selective_assert_safe_url):
        res = await authed_client.post(
            "/ingest/url",
            json={"url": "https://safe-looking-site.com/page"},
        )

    assert res.status_code == 400
    detail = res.json()["detail"].lower()
    assert "not allowed" in detail or "private" in detail


@pytest.mark.asyncio
async def test_assert_safe_url_rejects_link_local():
    """Unit test: _assert_safe_url must reject link-local IPs directly."""
    from app.services.ingest import _assert_safe_url

    with pytest.raises(ValueError, match="not allowed"):
        await _assert_safe_url("http://169.254.169.254/latest/meta-data/")

# ---------------------------------------------------------------------------
# R-07: Ingest router does not leak raw exception messages to clients
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ingest_url_unexpected_error_returns_generic_message(
    authed_client: AsyncClient,
):
    """Unexpected exceptions must return a generic message, not raw str(e)."""
    from unittest.mock import patch, AsyncMock

    # Patch at the router's import site — where the name is looked up at call time
    with patch(
        "app.routers.ingest.fetch_and_clean_url",
        new=AsyncMock(side_effect=RuntimeError("internal db connection pool exhausted")),
    ):
        res = await authed_client.post(
            "/ingest/url",
            json={"url": "https://example.com/article"},
        )

    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "db connection pool" not in detail.lower(), (
        "Ingest router must not leak raw exception messages to clients"
    )
    assert "try again" in detail.lower() or "failed" in detail.lower()


@pytest.mark.asyncio
async def test_ingest_text_unexpected_error_returns_generic_message(
    authed_client: AsyncClient,
):
    """Unexpected text ingest exceptions must not expose internal details."""
    from unittest.mock import patch, AsyncMock

    with patch(
        "app.routers.ingest.ingest_text_document",
        new=AsyncMock(side_effect=RuntimeError("filesystem quota exceeded")),
    ):
        res = await authed_client.post(
            "/ingest/text",
            json={"text": "Some article text here. " * 10, "title": "Test"},
        )

    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "filesystem quota" not in detail.lower(), (
        "Ingest router must not leak raw exception messages to clients"
    )
    assert "try again" in detail.lower() or "failed" in detail.lower()


@pytest.mark.asyncio
async def test_ingest_url_value_error_is_surfaced(authed_client: AsyncClient):
    """ValueError (user-facing validation) must be returned as-is to the client."""
    from unittest.mock import patch, AsyncMock

    # Patch at router import site so the ValueError reaches the router's except ValueError handler
    with patch(
        "app.routers.ingest.fetch_and_clean_url",
        new=AsyncMock(side_effect=ValueError("URL returned unsupported content type 'application/pdf'")),
    ):
        res = await authed_client.post(
            "/ingest/url",
            json={"url": "https://example.com/file.pdf"},
        )

    assert res.status_code == 400
    assert "application/pdf" in res.json()["detail"]