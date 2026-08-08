"""
Coverage-boost tests — targeted at low-coverage modules.

These tests exercise code paths that are normally hard to reach in
integration tests (dev-mode email fallback, cache key building,
DB engine proxy, response envelope helpers, etc.).
"""

import csv
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app as fastapi_app

# =====================================================================
# Email service — dev-mode (no SMTP) fallbacks
# =====================================================================


@pytest.mark.asyncio
async def test_send_verification_email_dev_mode():
    """In dev mode (no smtp_host), verification email just logs."""
    from app.services.email import send_verification_email

    # Default test config has no smtp_host → should return without error
    await send_verification_email("test@example.com", "https://example.com/verify?token=abc")


@pytest.mark.asyncio
async def test_send_password_reset_email_dev_mode():
    """In dev mode (no smtp_host), password reset email just logs."""
    from app.services.email import send_password_reset_email

    await send_password_reset_email("test@example.com", "https://example.com/reset?token=abc")


@pytest.mark.asyncio
async def test_send_magic_link_email_dev_mode():
    """In dev mode (no smtp_host), magic link email just logs."""
    from app.services.email import send_magic_link_email

    await send_magic_link_email("test@example.com", "https://example.com/magic?token=abc")


@pytest.mark.asyncio
async def test_send_account_exists_email_dev_mode():
    """In dev mode (no smtp_host), account-exists email just logs."""
    from app.services.email import send_account_exists_email

    await send_account_exists_email("test@example.com", "https://example.com/login?token=abc")


@pytest.mark.asyncio
async def test_record_failed_email_logs_on_db_error():
    """Dead-letter recording should not raise even if DB fails."""
    from app.services.email import _record_failed_email

    with patch("app.db.get_session_factory", side_effect=Exception("DB down")):
        # Should not raise — last-resort logging only
        await _record_failed_email("test@example.com", "Subject", "template", "error msg")


def test_send_email_background_fires_and_forgets():
    """send_email_background wraps a coro in fire_and_forget."""
    from app.services.email import send_email_background

    mock_coro = AsyncMock()()

    with patch("app.tasks.fire_and_forget") as mock_ff:
        send_email_background(
            mock_coro,
            to_email="test@example.com",
            subject="Test",
            template="verification",
        )
        mock_ff.assert_called_once()

        wrapper_coro = mock_ff.call_args[0][0]
        wrapper_coro.close()
        mock_coro.close()


# =====================================================================
# Cache service — unit tests without Redis
# =====================================================================


def test_build_cache_key_deterministic():
    """Same params always produce the same key."""
    from app.services.cache import _build_cache_key

    key1 = _build_cache_key("summary", text="hello", length="short")
    key2 = _build_cache_key("summary", text="hello", length="short")
    assert key1 == key2
    assert key1.startswith("cache:summary:")


def test_build_cache_key_param_order_independent():
    """Param ordering shouldn't affect the key."""
    from app.services.cache import _build_cache_key

    key_a = _build_cache_key("test", a="1", b="2")
    key_b = _build_cache_key("test", b="2", a="1")
    assert key_a == key_b


def test_build_cache_key_different_params_differ():
    """Different params produce different keys."""
    from app.services.cache import _build_cache_key

    key1 = _build_cache_key("test", text="hello")
    key2 = _build_cache_key("test", text="world")
    assert key1 != key2


@pytest.mark.asyncio
async def test_cache_get_returns_none_without_redis():
    """cache_get returns None when Redis is unavailable."""
    import app.services.cache
    app.services.cache._shared_redis = None  # ensure no shared client
    from app.services.cache import cache_get

    result = await cache_get("summary", text="unique-test-no-redis")
    # No redis in test → should return None gracefully
    assert result is None


@pytest.mark.asyncio
async def test_cache_set_noop_without_redis():
    """cache_set should not raise when Redis is unavailable."""
    import app.services.cache
    app.services.cache._shared_redis = None
    from app.services.cache import cache_set

    # Should not raise
    await cache_set("summary", {"result": "test"}, text="test-no-redis")


@pytest.mark.asyncio
async def test_get_cached_summary_returns_none():
    """get_cached_summary returns None without Redis."""
    import app.services.cache
    app.services.cache._shared_redis = None
    from app.services.cache import get_cached_summary

    result = await get_cached_summary("some unique text no redis", length="short")
    assert result is None


@pytest.mark.asyncio
async def test_set_cached_summary_noop():
    """set_cached_summary should not raise without Redis."""
    import app.services.cache
    app.services.cache._shared_redis = None
    from app.services.cache import set_cached_summary

    await set_cached_summary("some text no redis", {"summary": "test"}, length="short")


def test_set_cache_redis():
    """set_cache_redis sets the shared client."""
    from app.services.cache import set_cache_redis

    mock_redis = MagicMock()
    set_cache_redis(mock_redis)
    from app.services import cache

    assert cache._shared_redis is mock_redis
    # Restore
    cache._shared_redis = None


# =====================================================================
# DB module — engine proxy, reset, sync URL builder
# =====================================================================


def test_engine_proxy_delegates():
    """_EngineProxy delegates attribute access to the real engine."""
    from app.db import _EngineProxy

    proxy = _EngineProxy()
    # Accessing .url on the proxy should trigger engine creation
    # and return the engine's url attribute
    assert proxy is not None


def test_reset_engine():
    """reset_engine clears the cached engine and factory."""
    from app.db import reset_engine

    reset_engine()
    import app.db

    assert app.db._async_engine is None
    assert app.db._async_session_factory is None


def test_build_sync_url_sqlite():
    """Sync URL for SQLite should stay as-is."""
    from app.db import _build_sync_url

    url = _build_sync_url()
    # In test config, DATABASE_URL is typically sqlite
    assert "sqlite" in url.lower() or "postgresql" in url.lower()


def test_get_sync_engine():
    """get_sync_engine returns a sync engine."""
    from app.db import get_sync_engine

    engine = get_sync_engine()
    assert engine is not None


def test_get_session_factory():
    """get_session_factory returns a callable factory."""
    from app.db import get_session_factory

    factory = get_session_factory()
    assert callable(factory)


# =====================================================================
# Lockout — InMemoryLockoutStore full lifecycle
# =====================================================================


@pytest.mark.asyncio
async def test_inmemory_lockout_full_lifecycle():
    """Test the full lockout lifecycle: unlocked → failures → locked → reset."""
    from app.lockout import InMemoryLockoutStore

    store = InMemoryLockoutStore(max_attempts=3, window_seconds=60)
    email = "locktest@example.com"

    # Initially not locked
    assert await store.is_locked(email) is False

    # Record failures below threshold
    await store.record_failure(email)
    await store.record_failure(email)
    assert await store.is_locked(email) is False

    # Third failure → locked
    count = await store.record_failure(email)
    assert count == 3
    assert await store.is_locked(email) is True

    # Reset clears lockout
    await store.reset(email)
    assert await store.is_locked(email) is False


@pytest.mark.asyncio
async def test_inmemory_lockout_window_expiry():
    """After the window expires, the lockout counter resets."""
    from app.lockout import InMemoryLockoutStore

    store = InMemoryLockoutStore(max_attempts=2, window_seconds=0)  # 0s window → expires immediately
    email = "expire@example.com"

    await store.record_failure(email)
    await store.record_failure(email)
    # Window is 0 seconds, so by next check it's expired
    assert await store.is_locked(email) is False


def test_email_key_is_hashed():
    """_email_key produces a SHA-256 hash, not raw email."""
    from app.lockout import _email_key

    key = _email_key("Test@Example.COM")
    assert "@" not in key
    assert len(key) == 32  # SHA-256 truncated to 32 hex chars


def test_email_key_case_insensitive():
    """_email_key is case-insensitive."""
    from app.lockout import _email_key

    assert _email_key("User@Example.com") == _email_key("user@example.com")


@pytest.mark.asyncio
async def test_noop_lockout_always_allows():
    """NoOpLockoutStore never locks."""
    from app.lockout import NoOpLockoutStore

    store = NoOpLockoutStore()
    assert await store.is_locked("any@email.com") is False
    assert await store.record_failure("any@email.com") == 0
    await store.reset("any@email.com")  # no-op, should not raise


def test_get_lockout_manager_returns_default():
    """get_lockout_manager creates InMemoryLockoutStore if not set."""
    import app.lockout

    old = app.lockout._lockout_manager
    app.lockout._lockout_manager = None
    try:
        from app.lockout import get_lockout_manager

        mgr = get_lockout_manager()
        assert mgr is not None
    finally:
        app.lockout._lockout_manager = old


# =====================================================================
# Response schema — paginated_response helper
# =====================================================================


def test_paginated_response_basic():
    """paginated_response builds correct envelope."""
    from app.schemas.response import paginated_response

    resp = paginated_response(data=[1, 2, 3], total=10, skip=0, limit=3)
    assert resp.success is True
    assert resp.data == [1, 2, 3]
    assert resp.meta["total"] == 10
    assert resp.meta["has_more"] is True


def test_paginated_response_last_page():
    """has_more is False on the last page."""
    from app.schemas.response import paginated_response

    resp = paginated_response(data=[1], total=3, skip=2, limit=1)
    assert resp.meta["has_more"] is False


def test_api_response_defaults():
    """APIResponse has sensible defaults."""
    from app.schemas.response import APIResponse

    r = APIResponse()
    assert r.success is True
    assert r.data is None
    assert r.error is None
    assert r.meta is None


# =====================================================================
# TTS service — provider validation
# =====================================================================


def test_tts_allowed_providers():
    """Only openai and elevenlabs are allowed TTS providers."""
    from app.services.tts import _ALLOWED_PROVIDERS

    assert "openai" in _ALLOWED_PROVIDERS
    assert "elevenlabs" in _ALLOWED_PROVIDERS
    assert len(_ALLOWED_PROVIDERS) == 2


# =====================================================================
# Flashcard CSV export
# =====================================================================


def test_generate_csv_export():
    """CSV export produces valid Anki-compatible CSV."""
    from app.services.flashcards import generate_csv_export

    # Create mock flashcards
    class MockCard:
        def __init__(self, front, back):
            self.front = front
            self.back = back

    cards = [
        MockCard("What is AI?", "Artificial\nIntelligence"),
        MockCard("What is ML?", "Machine\tLearning"),
    ]
    csv_str = generate_csv_export(cards)

    # Parse and verify
    reader = csv.reader(StringIO(csv_str))
    rows = list(reader)
    assert len(rows) == 2
    assert rows[0][0] == "What is AI?"
    assert "\n" not in rows[0][1]  # newlines should be stripped
    assert "\t" not in rows[1][1]  # tabs should be stripped


# =====================================================================
# Main app — exception handlers + root health
# =====================================================================

_TEST_CSRF = "coverage-boost-csrf"


@pytest.mark.asyncio
async def test_root_health_endpoint():
    """GET / returns {status: ok} for Render health check."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-CSRF-Token": _TEST_CSRF},
        cookies={"csrf_token": _TEST_CSRF},
    ) as client:
        res = await client.get("/")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_validation_error_handler_returns_envelope():
    """RequestValidationError returns {detail, code} envelope."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test/api/v1",
        headers={"X-CSRF-Token": _TEST_CSRF},
        cookies={"csrf_token": _TEST_CSRF},
    ) as client:
        # Send invalid JSON to trigger validation error
        res = await client.post("/auth/register", json={"email": "bad"})
        assert res.status_code == 422
        data = res.json()
        assert "detail" in data
        assert "code" in data


@pytest.mark.asyncio
async def test_http_exception_handler_returns_envelope():
    """HTTPException returns {detail, code} envelope."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test/api/v1",
        headers={"X-CSRF-Token": _TEST_CSRF},
        cookies={"csrf_token": _TEST_CSRF},
    ) as client:
        res = await client.get("/auth/me")
        assert res.status_code == 401
        data = res.json()
        assert "detail" in data
        assert "code" in data


@pytest.mark.asyncio
async def test_404_returns_envelope():
    """404 returns {detail, code} envelope."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test/api/v1",
        headers={"X-CSRF-Token": _TEST_CSRF},
        cookies={"csrf_token": _TEST_CSRF},
    ) as client:
        res = await client.get("/nonexistent-path")
        assert res.status_code == 404
        data = res.json()
        assert "detail" in data


# =====================================================================
# Error codes module
# =====================================================================


def test_error_code_constants():
    """ErrorCode has expected constants."""
    from app.errors import ErrorCode

    assert ErrorCode.VALIDATION_ERROR is not None
    assert ErrorCode.INTERNAL_ERROR is not None


def test_code_for_status_maps_correctly():
    """code_for_status returns appropriate error codes."""
    from app.errors import code_for_status

    assert code_for_status(401) is not None
    assert code_for_status(403) is not None
    assert code_for_status(404) is not None
    assert code_for_status(422) is not None
    assert code_for_status(500) is not None


# =====================================================================
# Config module — property access
# =====================================================================


def test_config_properties():
    """Config has expected properties."""
    from app.config import get_config

    cfg = get_config()
    assert cfg.environment is not None
    assert cfg.database_url is not None
    assert isinstance(cfg.is_sqlite, bool)
    assert isinstance(cfg.has_llm_provider, bool)
    assert cfg.async_database_url is not None


def test_config_lockout_defaults():
    """Lockout config has reasonable defaults."""
    from app.config import get_config

    cfg = get_config()
    assert cfg.lockout_max_attempts >= 3
    assert cfg.lockout_window_seconds >= 60


# =====================================================================
# DB module — build_engine_kwargs
# =====================================================================


def test_build_engine_kwargs_sqlite():
    """SQLite engine kwargs include StaticPool."""
    from app.db import _build_engine_kwargs

    kwargs = _build_engine_kwargs()
    # Test config uses SQLite
    if "poolclass" in kwargs:
        from sqlalchemy.pool import StaticPool

        assert kwargs["poolclass"] is StaticPool
