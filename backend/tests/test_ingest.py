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
