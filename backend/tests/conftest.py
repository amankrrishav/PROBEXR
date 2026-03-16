"""
conftest.py — shared fixtures for backend smoke tests.

Provides:
  - async_session: in-memory SQLite session for DB tests
  - client: async FastAPI test client
  - registered_user: a pre-registered AND email-verified user with token
"""
import asyncio
from typing import AsyncGenerator
from datetime import datetime, timezone, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

import app.models  # noqa: F401 — register all models on metadata
from app.db import get_session
from app.main import app as fastapi_app
from app.middleware import set_rate_limiter
from app.config import get_config
from app.services.auth import create_email_verification_token
import jwt as jose_jwt


# ---- Disable rate limiting in tests ----

class _NoOpRateLimiter:
    """Rate limiter that always allows — prevents 429s in tests."""
    async def check_and_increment(self, key: str, limit: int) -> tuple[bool, int]:
        return True, 0

set_rate_limiter(_NoOpRateLimiter())

# ---- CSRF test token ----
# All test clients will include this matching cookie + header pair
# so the CSRFMiddleware allows requests through.
_TEST_CSRF_TOKEN = "test-csrf-token-for-testing"


# ---- In-memory async engine for testing ----

_test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

_TestSessionLocal = async_sessionmaker(
    _test_engine, class_=AsyncSession, expire_on_commit=False
)


async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSessionLocal() as session:
        yield session


fastapi_app.dependency_overrides[get_session] = _override_get_session


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def _setup_db():
    """Create all tables before each test, drop after."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test/api/v1",
        headers={"X-CSRF-Token": _TEST_CSRF_TOKEN},
        cookies={"csrf_token": _TEST_CSRF_TOKEN},
    ) as c:
        yield c


def make_oauth_state(provider: str = "google") -> str:
    """Create a valid JWT-signed OAuth state token for tests."""
    cfg = get_config()
    payload = {"provider": provider, "exp": datetime.now(timezone.utc) + timedelta(minutes=10)}
    return jose_jwt.encode(payload, cfg.secret_key, algorithm=cfg.algorithm)


async def verify_user_email(client: AsyncClient, email: str) -> None:
    """Helper: generate a verification token and call the verify-email endpoint."""
    token = create_email_verification_token(email)
    res = await client.get(f"/auth/verify-email?token={token}")
    assert res.status_code == 200, f"Email verification failed for {email}: {res.text}"


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict:
    """Register a user, verify their email, and return credentials.

    All feature routes now require is_verified=True (VerifiedUser dep),
    so we verify immediately after registration to avoid 403s in tests.
    """
    email = "test@example.com"
    password = "TestPass123!"
    res = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert res.status_code == 201, f"Registration failed: {res.text}"
    data = res.json()

    # Verify email so VerifiedUser dependency passes
    await verify_user_email(client, email)

    return {
        "email": email,
        "password": password,
        "token": data["access_token"],
        "refresh_token": data.get("refresh_token"),
        "cookies": res.cookies,
    }


@pytest_asyncio.fixture
async def authed_client(client: AsyncClient, registered_user: dict) -> AsyncClient:
    """Client with access_token cookie pre-set — ready for authenticated requests."""
    client.cookies.set("access_token", f"Bearer {registered_user['token']}")
    return client


@pytest_asyncio.fixture
async def document_id(authed_client: AsyncClient) -> int:
    """Ingest a test document and return its ID."""
    sample_text = (
        "Artificial intelligence has transformed the technology landscape dramatically. "
        "Machine learning algorithms now power recommendation systems, natural language processing, "
        "and computer vision applications across industries. Researchers continue to push "
        "the boundaries of what is possible with deep learning architectures. Companies invest "
        "billions of dollars annually in AI research and development. The impact of these "
        "technologies extends beyond the tech sector into healthcare, finance, education, and "
        "manufacturing. Despite rapid progress, significant challenges remain in areas such as "
        "model interpretability, data privacy, and ethical deployment."
    )
    res = await authed_client.post(
        "/ingest/text",
        json={"text": sample_text, "title": "Test AI Article"},
    )
    assert res.status_code == 200
    return res.json()["id"]