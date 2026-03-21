"""
Flashcard endpoint tests — listing, creation auth guard, export auth guard.
Flashcard generation requires LLM, so we test auth/validation guards and listing.
"""
import pytest
from httpx import AsyncClient


# ---- GET /api/flashcards/ ----

@pytest.mark.asyncio
async def test_list_flashcard_sets_empty(authed_client: AsyncClient):
    """New user has no flashcard sets."""
    res = await authed_client.get("/flashcards/")
    assert res.status_code == 200
    data = res.json()
    assert data["flashcard_sets"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert "pages" in data


@pytest.mark.asyncio
async def test_list_flashcard_sets_unauthenticated(client: AsyncClient):
    res = await client.get("/flashcards/")
    assert res.status_code == 401


# ---- POST /api/flashcards/ ----

@pytest.mark.asyncio
async def test_create_flashcards_unauthenticated(client: AsyncClient):
    res = await client.post(
        "/flashcards/",
        json={"document_id": 1, "count": 5},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_create_flashcards_document_not_found(authed_client: AsyncClient):
    """Non-existent document returns error."""
    res = await authed_client.post(
        "/flashcards/",
        json={"document_id": 999999, "count": 5},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_create_flashcards_invalid_count(authed_client: AsyncClient, document_id: int):
    """Count outside 1-50 range triggers validation."""
    res = await authed_client.post(
        "/flashcards/",
        json={"document_id": document_id, "count": 100},
    )
    assert res.status_code == 422


# ---- GET /api/flashcards/{set_id}/export ----

@pytest.mark.asyncio
async def test_export_flashcards_unauthenticated(client: AsyncClient):
    res = await client.get("/flashcards/1/export")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_export_flashcards_not_found(authed_client: AsyncClient):
    """Non-existent flashcard set returns 404."""
    res = await authed_client.get("/flashcards/999999/export")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# A-06: LLM provider guard — missing key returns safe 400, not internal error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_flashcards_no_llm_provider_returns_400(
    authed_client: AsyncClient, document_id: int
):
    """
    When no LLM provider is configured (test env has no API keys),
    the endpoint must return 400 with a user-safe message — NOT a 500
    leaking the internal ValueError from config.get_llm_base_url().
    """
    from unittest.mock import PropertyMock, patch
    with patch("app.services.flashcards.get_config") as mock_cfg:
        mock_cfg.return_value.has_llm_provider = False
        res = await authed_client.post(
            "/flashcards/",
            json={"document_id": document_id, "count": 5},
        )
    # Must be 400 (user-safe), not 500 (internal leak)
    assert res.status_code == 400
    detail = res.json()["detail"].lower()
    # Must mention LLM provider in a user-friendly way
    assert "llm provider" in detail or "api key" in detail
    # Must NOT leak the raw internal config error message
    assert "get_llm_base_url" not in detail
    assert "get_llm_api_key" not in detail


@pytest.mark.asyncio
async def test_create_flashcards_no_llm_error_message_is_actionable(
    authed_client: AsyncClient, document_id: int
):
    """Error message tells the user what to do (set an API key)."""
    from unittest.mock import patch
    with patch("app.services.flashcards.get_config") as mock_cfg:
        mock_cfg.return_value.has_llm_provider = False
        res = await authed_client.post(
            "/flashcards/",
            json={"document_id": document_id, "count": 5},
        )
    assert res.status_code == 400
    detail = res.json()["detail"].lower()
    # Should mention setting a key — actionable guidance
    assert "groq_api_key" in detail or "openai_api_key" in detail or "api key" in detail


# ---------------------------------------------------------------------------
# N-07: list_flashcard_sets uses a single aggregated query (no N+1)
# ---------------------------------------------------------------------------

def test_list_flashcard_sets_no_loop_query():
    """list_flashcard_sets must aggregate card counts in one query, not per-set loops."""
    import inspect
    from app.routers import flashcards as fc_router
    src = inspect.getsource(fc_router.list_flashcard_sets)
    # New pattern: single IN query with GROUP BY before the loop
    assert 'set_ids' in src, (
        "list_flashcard_sets must batch card count lookup using set_ids"
    )
    assert '.in_(set_ids)' in src, (
        "list_flashcard_sets must use .in_(set_ids) to batch the card count query"
    )
    # The loop must only build the response list — no DB call inside it.
    # Check that 'await session.execute' does NOT appear after 'for s in sets:'
    loop_start = src.find('for s in sets:')
    assert loop_start != -1, "Expected 'for s in sets:' loop in list_flashcard_sets"
    src_after_loop = src[loop_start:]
    assert 'await session.execute' not in src_after_loop, (
        "list_flashcard_sets must not call session.execute() inside the 'for s in sets' loop"
    )


# ---------------------------------------------------------------------------
# R-05: Flashcard.front and Flashcard.back have max_length bounds
# ---------------------------------------------------------------------------

def test_flashcard_front_has_max_length():
    """Flashcard.front must have a max_length constraint."""
    src = open('app/models/flashcards.py').read()
    front_lines = [l for l in src.split('\n') if 'front' in l and 'Field' in l]
    assert front_lines, "Flashcard must have a front field with Field()"
    assert any('max_length' in l for l in front_lines), (
        f"Flashcard.front must have max_length. Found: {front_lines}"
    )


def test_flashcard_back_has_max_length():
    """Flashcard.back must have a max_length constraint."""
    src = open('app/models/flashcards.py').read()
    back_lines = [l for l in src.split('\n') if "'back'" in l or ('"back"' in l) or ('back' in l and 'Field' in l and 'set_id' not in l and 'flashcard_set' not in l)]
    back_field_lines = [l for l in src.split('\n') if l.strip().startswith('back') and 'Field' in l]
    assert back_field_lines, "Flashcard must have a back field with Field()"
    assert any('max_length' in l for l in back_field_lines), (
        f"Flashcard.back must have max_length. Found: {back_field_lines}"
    )