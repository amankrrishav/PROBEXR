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


# ---------------------------------------------------------------------------
# N-11: assert session_id is not None replaced with proper ValueError guard
# ---------------------------------------------------------------------------

def test_prepare_chat_context_uses_value_error_not_assert():
    """prepare_chat_context must raise ValueError, not assert, for missing session_id."""
    import inspect
    from app.services import chat
    src = inspect.getsource(chat.prepare_chat_context)
    assert 'assert session_id' not in src, (
        "assert session_id is not None must be replaced with an explicit ValueError guard"
    )
    assert 'session_id is None' in src, (
        "prepare_chat_context must have an explicit session_id is None check"
    )


# ---------------------------------------------------------------------------
# N-07: list_chat_sessions uses a single aggregated query (no N+1)
# ---------------------------------------------------------------------------

def test_list_chat_sessions_no_loop_query():
    """list_chat_sessions must not execute a DB query per session in a loop."""
    import inspect
    from app.routers import chat as chat_router
    src = inspect.getsource(chat_router.list_chat_sessions)
    # The old N+1 pattern: for s in sessions_list: await session.execute(...)
    # New pattern uses outerjoin + GROUP BY in a single query
    assert 'outerjoin' in src, (
        "list_chat_sessions must use outerjoin to avoid N+1 queries"
    )
    # Must NOT contain a per-row execute inside the loop
    assert 'for s in sessions_list' not in src, (
        "list_chat_sessions must not loop over sessions and query each one individually"
    )