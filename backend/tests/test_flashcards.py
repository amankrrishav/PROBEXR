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
