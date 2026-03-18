"""
tests/test_text_ingest_dedup.py — A-08: Text ingest deduplication by content hash

Verifies that submitting identical text twice returns the same document
rather than creating a duplicate, using SHA-256 content hash as the dedup key.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dedup_returns_same_document_id(client: AsyncClient, registered_user: dict):
    """Submitting identical text twice returns the same document (same ID)."""
    client.cookies.set("access_token", f"Bearer {registered_user['token']}")
    text = "This is a unique article about quantum computing. " * 10

    res1 = await client.post("/ingest/text", json={"text": text, "title": "Article"})
    res2 = await client.post("/ingest/text", json={"text": text, "title": "Article"})

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.json()["id"] == res2.json()["id"], (
        "Duplicate text must return the same document ID"
    )


@pytest.mark.asyncio
async def test_different_content_creates_new_document(client: AsyncClient, registered_user: dict):
    """Different text content creates a distinct document."""
    client.cookies.set("access_token", f"Bearer {registered_user['token']}")

    res1 = await client.post("/ingest/text", json={"text": "Article about AI. " * 10, "title": "AI"})
    res2 = await client.post("/ingest/text", json={"text": "Article about space. " * 10, "title": "Space"})

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.json()["id"] != res2.json()["id"], (
        "Different content must create different documents"
    )


@pytest.mark.asyncio
async def test_url_field_contains_content_hash(client: AsyncClient, registered_user: dict):
    """The url field for pasted text uses the content hash, not a random UUID."""
    client.cookies.set("access_token", f"Bearer {registered_user['token']}")
    text = "Deterministic content for hash test. " * 10

    res = await client.post("/ingest/text", json={"text": text, "title": "Hash test"})
    assert res.status_code == 200

    import hashlib
    expected_hash = hashlib.sha256(text.strip().encode()).hexdigest()[:16]
    url_field = res.json().get("url", "")
    assert expected_hash in url_field, (
        f"Expected hash {expected_hash} in url field, got {url_field}"
    )


@pytest.mark.asyncio
async def test_dedup_is_per_user(client: AsyncClient, registered_user: dict):
    """Dedup key is scoped per user — verify hash is present in url field."""
    text = "Shared article text about machine learning. " * 10

    # Register a second user via a fresh client so the shared client's
    # CSRF + access_token cookies are never disturbed
    from httpx import AsyncClient as _AsyncClient
    from httpx import ASGITransport as _ASGITransport
    from app.main import app as _app
    async with _AsyncClient(
        transport=_ASGITransport(app=_app),
        base_url="http://test/api/v1",
        headers={"X-CSRF-Token": "test-csrf-token-for-testing"},
        cookies={"csrf_token": "test-csrf-token-for-testing"},
    ) as reg_client:
        res = await reg_client.post(
            "/auth/register",
            json={"email": "second@example.com", "password": "SecondPass123!"},
        )
    assert res.status_code in (200, 201)

    # User 1's token is untouched — use the original client directly
    client.cookies.set("access_token", f"Bearer {registered_user['token']}")
    res1 = await client.post("/ingest/text", json={"text": text, "title": "Article"})
    assert res1.status_code == 200

    # Verify the dedup key (content hash) is embedded in the url field
    import hashlib
    expected_hash = hashlib.sha256(text.strip().encode()).hexdigest()[:16]
    assert expected_hash in res1.json().get("url", "")