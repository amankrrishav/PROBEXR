"""
Analytics endpoint tests — dashboard metrics, auth guards, empty/populated states.
"""
import pytest
from httpx import AsyncClient


# ---- Auth Guard ----

@pytest.mark.asyncio
async def test_analytics_unauthenticated(client: AsyncClient):
    """Dashboard requires authentication."""
    res = await client.get("/analytics/dashboard")
    assert res.status_code == 401


# ---- Empty State ----

@pytest.mark.asyncio
async def test_analytics_empty(authed_client: AsyncClient):
    """New user with no data gets zero counts and empty arrays."""
    res = await authed_client.get("/analytics/dashboard")
    assert res.status_code == 200
    data = res.json()

    # Structure check
    assert "summary_stats" in data
    assert "activity_heatmap" in data
    assert "top_domains" in data
    assert "streak" in data

    stats = data["summary_stats"]
    assert stats["total_documents"] == 0
    assert stats["total_words"] == 0
    assert stats["time_saved_seconds"] == 0
    assert stats["total_flashcard_sets"] == 0
    assert stats["total_flashcards"] == 0
    assert stats["total_chat_sessions"] == 0
    assert stats["total_chat_messages"] == 0

    # Heatmap should be 365 days
    assert len(data["activity_heatmap"]) == 365

    # No domains, no streak
    assert data["top_domains"] == []
    assert data["streak"] == 0


# ---- With Data ----

@pytest.mark.asyncio
async def test_analytics_with_documents(authed_client: AsyncClient, document_id: int):
    """After ingesting a document, stats reflect it."""
    res = await authed_client.get("/analytics/dashboard")
    assert res.status_code == 200
    data = res.json()

    stats = data["summary_stats"]
    assert stats["total_documents"] >= 1
    assert stats["total_words"] > 0
    assert stats["time_saved_seconds"] > 0

    # Today should have at least 1 in heatmap
    heatmap = data["activity_heatmap"]
    today_entry = heatmap[-1]  # Last entry = today
    assert today_entry["count"] >= 1


@pytest.mark.asyncio
async def test_analytics_with_multiple_documents(authed_client: AsyncClient):
    """Multiple documents are counted correctly."""
    # Ingest 3 documents
    for i in range(3):
        res = await authed_client.post(
            "/ingest/text",
            json={"text": f"Document number {i} about testing analytics. " * 20, "title": f"Analytics Doc {i}"},
        )
        assert res.status_code == 200

    res = await authed_client.get("/analytics/dashboard")
    assert res.status_code == 200
    data = res.json()

    stats = data["summary_stats"]
    assert stats["total_documents"] == 3
    assert stats["total_words"] > 0

    # Top domains should include "Pasted Text" since they're text ingests
    domains = data["top_domains"]
    pasted = [d for d in domains if d["domain"] == "Pasted Text"]
    assert len(pasted) == 1
    assert pasted[0]["count"] == 3


@pytest.mark.asyncio
async def test_analytics_streak(authed_client: AsyncClient, document_id: int):
    """Streak should be at least 1 when a document was ingested today."""
    res = await authed_client.get("/analytics/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert data["streak"] >= 1


@pytest.mark.asyncio
async def test_analytics_streak_survives_no_activity_today(authed_client: AsyncClient):
    """
    A streak built on previous days should not reset to 0 just because
    the user hasn't ingested anything yet today.
    We simulate this by ingesting a document then backdating its created_at
    to yesterday, then verifying the streak is still >= 1.
    """
    from datetime import datetime, timezone, timedelta
    from app.models.document import Document
    from tests.conftest import _TestSessionLocal

    # Ingest a document
    res = await authed_client.post(
        "/ingest/text",
        json={"text": "Yesterday document for streak test. " * 10, "title": "Yesterday Doc"},
    )
    assert res.status_code == 200
    doc_id = res.json()["id"]

    # Backdate via the test session (same DB the app uses in tests)
    async with _TestSessionLocal() as session:
        doc = await session.get(Document, doc_id)
        if doc:
            doc.created_at = (datetime.now(timezone.utc) - timedelta(days=1)).replace(tzinfo=None)
            session.add(doc)
            await session.commit()

    res = await authed_client.get("/analytics/dashboard")
    assert res.status_code == 200
    data = res.json()
    # Streak should be >= 1 even though nothing ingested today
    assert data["streak"] >= 1


@pytest.mark.asyncio
async def test_analytics_heatmap_structure(authed_client: AsyncClient):
    """Heatmap entries have correct structure."""
    res = await authed_client.get("/analytics/dashboard")
    assert res.status_code == 200
    data = res.json()

    heatmap = data["activity_heatmap"]
    assert len(heatmap) == 365

    # Each entry should have date and count
    for entry in heatmap:
        assert "date" in entry
        assert "count" in entry
        assert isinstance(entry["count"], int)
        assert entry["count"] >= 0

# ---------------------------------------------------------------------------
# N-10: analytics router uses HTTPException not assert for user.id guard
# ---------------------------------------------------------------------------

def test_analytics_router_no_assert_on_user_id():
    """dashboard route must not use assert for user.id — assert is stripped by -O."""
    import inspect
    from app.routers import analytics as analytics_router
    src = inspect.getsource(analytics_router.dashboard)
    assert 'assert user.id' not in src, (
        "assert user.id is not None is stripped by Python -O. "
        "Use an explicit HTTPException guard instead."
    )
    assert 'HTTPException' in src or 'user.id is None' in src, (
        "dashboard must have an explicit user.id None check"
    )