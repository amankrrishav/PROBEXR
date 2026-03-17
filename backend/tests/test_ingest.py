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


@pytest.mark.asyncio
async def test_ingest_url_private_ip_blocked(client: AsyncClient, registered_user: dict):
    """SSRF protection: private IPs must be rejected."""
    client.cookies.set("access_token", f"Bearer {registered_user['token']}")
    res = await client.post(
        "/ingest/url",
        json={"url": "http://127.0.0.1/secret"},
    )
    assert res.status_code == 400
    assert "private" in res.json()["detail"].lower() or "not allowed" in res.json()["detail"].lower()


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

