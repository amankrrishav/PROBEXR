"""
Contract tests — validate that API responses match expected schemas.

These tests ensure the frontend and backend stay in sync by verifying
that every API endpoint returns the exact shape of JSON the frontend expects.
They catch schema drift (e.g., renamed fields, missing keys, type changes)
before it reaches production.

Run with: pytest tests/test_api_contracts.py -v
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from app.db import get_session
from app.main import app
from tests.conftest import _override_get_session
from app.models import *  # noqa: F401,F403 — ensure all models are registered

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="module")
async def engine():
    eng = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as sess:
        yield sess


_TEST_CSRF_TOKEN = "contract-test-csrf-token"


@pytest_asyncio.fixture
async def client(session) -> AsyncGenerator[AsyncClient, None]:
    async def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"X-CSRF-Token": _TEST_CSRF_TOKEN},
        cookies={"csrf_token": _TEST_CSRF_TOKEN},
    ) as c:
        yield c
    app.dependency_overrides[get_session] = _override_get_session


# ---------------------------------------------------------------------------
# Health endpoint contracts
# ---------------------------------------------------------------------------


class TestHealthContracts:
    """Health endpoints return the exact shape the frontend dashboard expects."""

    @pytest.mark.asyncio
    async def test_liveness_schema(self, client: AsyncClient):
        r = await client.get("/api/v1/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert isinstance(data["status"], str)

    @pytest.mark.asyncio
    async def test_readiness_schema(self, client: AsyncClient):
        r = await client.get("/api/v1/ready")
        # May be 200 or 503 depending on DB state, but shape must be stable
        data = r.json()
        assert "ready" in data
        assert "checks" in data
        assert isinstance(data["checks"], dict)
        assert isinstance(data["ready"], bool)


# ---------------------------------------------------------------------------
# Auth endpoint contracts
# ---------------------------------------------------------------------------


class TestAuthContracts:
    """Auth endpoints return fields the frontend auth context expects."""

    @pytest.mark.asyncio
    async def test_register_returns_token(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/auth/register",
            json={"email": "contract@test.com", "password": "StrongP@ss123!"},
        )
        assert r.status_code == 201
        data = r.json()
        # Registration returns a Token for auto-login
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data

    @pytest.mark.asyncio
    async def test_login_failure_shape(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "noexist@test.com", "password": "wrong"},
        )
        assert r.status_code == 401
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


# ---------------------------------------------------------------------------
# Summarize endpoint contracts
# ---------------------------------------------------------------------------


class TestSummarizeContracts:
    """Summarize responses must include the fields the frontend renders."""

    @pytest.mark.asyncio
    async def test_summarize_validation_error_shape(self, client: AsyncClient):
        """Empty text should return 400/422 with detail."""
        r = await client.post("/api/v1/summarize", json={"text": ""})
        assert r.status_code in (400, 422)
        data = r.json()
        assert "detail" in data


# ---------------------------------------------------------------------------
# TTS status contract
# ---------------------------------------------------------------------------


class TestTTSContracts:
    """TTS status endpoint shape must match the frontend feature-flag check."""

    @pytest.mark.asyncio
    async def test_tts_status_shape(self, client: AsyncClient):
        r = await client.get("/api/v1/tts/status")
        assert r.status_code == 200
        data = r.json()
        assert "available" in data
        assert "message" in data
        assert isinstance(data["available"], bool)
        assert isinstance(data["message"], str)


# ---------------------------------------------------------------------------
# Metrics endpoint contract
# ---------------------------------------------------------------------------


class TestMetricsContracts:
    """Prometheus /metrics endpoint must return text/plain."""

    @pytest.mark.asyncio
    async def test_metrics_content_type(self, client: AsyncClient):
        r = await client.get("/api/v1/metrics")
        assert r.status_code == 200
        assert "text/plain" in r.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# Error shape contract
# ---------------------------------------------------------------------------


class TestErrorContracts:
    """All error responses must follow the {detail: str} shape."""

    @pytest.mark.asyncio
    async def test_404_shape(self, client: AsyncClient):
        r = await client.get("/nonexistent-route-abc123")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
