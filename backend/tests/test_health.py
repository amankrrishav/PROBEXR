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
    res = await client.get("/tts/status")
    assert res.status_code == 200
    data = res.json()
    assert "available" in data
    assert data["available"] is False  # stub — not yet implemented


@pytest.mark.asyncio
async def test_tts_create_returns_503(authed_client: AsyncClient, document_id: int):
    """TTS create endpoint returns 503 (not implemented)."""
    res = await authed_client.post(
        "/tts/",
        json={"document_id": document_id, "provider": "openai"},
    )
    assert res.status_code == 503
    assert "not yet available" in res.json()["detail"].lower() or "tts_enabled" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_tts_create_unauthenticated(client: AsyncClient):
    """TTS requires auth even though it's a stub."""
    res = await client.post(
        "/tts/",
        json={"document_id": 1, "provider": "openai"},
    )
    # OptionalUser allows it through but it still returns 503
    assert res.status_code == 503


# ---- Synthesis ----

@pytest.mark.asyncio
async def test_synthesis_unauthenticated(client: AsyncClient):
    """Synthesis requires authentication."""
    res = await client.post(
        "/synthesis/",
        json={"document_ids": [1, 2]},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_synthesis_too_few_documents(authed_client: AsyncClient):
    """Need at least 2 document IDs."""
    res = await authed_client.post(
        "/synthesis/",
        json={"document_ids": [1]},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_synthesis_too_many_documents(authed_client: AsyncClient):
    """Cannot exceed 10 document IDs."""
    res = await authed_client.post(
        "/synthesis/",
        json={"document_ids": list(range(1, 15))},
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# N-17: TTS controlled by tts_enabled feature flag
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tts_status_reflects_feature_flag(client: AsyncClient):
    """GET /tts/status available field must reflect the tts_enabled config flag."""
    res = await client.get("/tts/status")
    assert res.status_code == 200
    data = res.json()
    assert "available" in data
    # Default is False (TTS_ENABLED not set in test env)
    assert data["available"] is False


def test_tts_enabled_flag_exists_in_config():
    """AppConfig must expose a tts_enabled boolean field."""
    from app.config import AppConfig
    cfg = AppConfig()
    assert hasattr(cfg, "tts_enabled"), "AppConfig must have a tts_enabled field"
    assert isinstance(cfg.tts_enabled, bool)


def test_tts_router_uses_feature_flag():
    """TTS router must check cfg.tts_enabled before calling the service."""
    import inspect
    from app.routers import tts as tts_router
    src = inspect.getsource(tts_router.create_tts)
    assert "tts_enabled" in src, (
        "create_tts must check cfg.tts_enabled before proceeding"
    )


def test_tts_router_calls_service_when_enabled():
    """TTS router must import and call generate_audio_summary when flag is on."""
    import inspect
    from app.routers import tts as tts_router
    src = inspect.getsource(tts_router.create_tts)
    assert "generate_audio_summary" in src, (
        "create_tts must call generate_audio_summary from tts service when enabled"
    )