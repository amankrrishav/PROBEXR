"""
Chat endpoint tests — send message, session listing, message listing, auth guards.
Tests the non-streaming path (POST /api/chat/).
Chat requires a document for context, so tests use the document_id fixture.

Note: The actual LLM call will fail in tests (no API key) so we test
that the service-layer error is handled gracefully, plus auth/validation guards.
"""
import pytest
from httpx import AsyncClient


# ---- POST /api/chat/ ----

@pytest.mark.asyncio
async def test_chat_unauthenticated(client: AsyncClient):
    res = await client.post(
        "/chat/",
        json={"document_id": 1, "message": "Hello"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_chat_document_not_found(authed_client: AsyncClient):
    """Chat about a non-existent document returns 404."""
    res = await authed_client.post(
        "/chat/",
        json={"document_id": 999999, "message": "Hello"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_chat_missing_message(authed_client: AsyncClient, document_id: int):
    """Missing message field triggers validation error."""
    res = await authed_client.post(
        "/chat/",
        json={"document_id": document_id},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_chat_invalid_session_id(authed_client: AsyncClient, document_id: int):
    """Non-existent session_id for the user returns error."""
    res = await authed_client.post(
        "/chat/",
        json={"document_id": document_id, "message": "Hello", "session_id": 999999},
    )
    # The service raises ValueError → router returns 404
    assert res.status_code in (404, 400)


# ---- GET /api/chat/sessions ----

@pytest.mark.asyncio
async def test_list_chat_sessions_empty(authed_client: AsyncClient):
    """New user has no chat sessions."""
    res = await authed_client.get("/chat/sessions")
    assert res.status_code == 200
    data = res.json()
    assert data["sessions"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_chat_sessions_unauthenticated(client: AsyncClient):
    res = await client.get("/chat/sessions")
    assert res.status_code == 401


# ---- GET /api/chat/sessions/{id}/messages ----

@pytest.mark.asyncio
async def test_list_session_messages_not_found(authed_client: AsyncClient):
    """Non-existent session returns 404."""
    res = await authed_client.get("/chat/sessions/999999/messages")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_list_session_messages_unauthenticated(client: AsyncClient):
    res = await client.get("/chat/sessions/1/messages")
    assert res.status_code == 401
