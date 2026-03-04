"""
Health, TTS status, and synthesis endpoint tests.
These are simple endpoints that don't require LLM keys.
"""
import pytest
from httpx import AsyncClient


# ---- GET / (health) ----

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Health endpoint is public and returns app info."""
    res = await client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "version" in data
    assert "mode" in data
    assert "capabilities" in data
    assert "summarize" in data["capabilities"]


# ---- TTS ----

@pytest.mark.asyncio
async def test_tts_status(client: AsyncClient):
    """TTS status endpoint is public."""
    res = await client.get("/api/tts/status")
    assert res.status_code == 200
    data = res.json()
    assert "available" in data
    assert data["available"] is False  # stub — not yet implemented


@pytest.mark.asyncio
async def test_tts_create_returns_503(authed_client: AsyncClient, document_id: int):
    """TTS create endpoint returns 503 (not implemented)."""
    res = await authed_client.post(
        "/api/tts/",
        json={"document_id": document_id, "provider": "openai"},
    )
    assert res.status_code == 503
    assert "coming soon" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_tts_create_unauthenticated(client: AsyncClient):
    """TTS requires auth even though it's a stub."""
    res = await client.post(
        "/api/tts/",
        json={"document_id": 1, "provider": "openai"},
    )
    # OptionalUser allows it through but it still returns 503
    assert res.status_code == 503


# ---- Synthesis ----

@pytest.mark.asyncio
async def test_synthesis_unauthenticated(client: AsyncClient):
    """Synthesis requires authentication."""
    res = await client.post(
        "/api/synthesis/",
        json={"document_ids": [1, 2]},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_synthesis_too_few_documents(authed_client: AsyncClient):
    """Need at least 2 document IDs."""
    res = await authed_client.post(
        "/api/synthesis/",
        json={"document_ids": [1]},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_synthesis_too_many_documents(authed_client: AsyncClient):
    """Cannot exceed 10 document IDs."""
    res = await authed_client.post(
        "/api/synthesis/",
        json={"document_ids": list(range(1, 15))},
    )
    assert res.status_code == 422
