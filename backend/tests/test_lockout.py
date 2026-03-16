"""
test_lockout.py — Account lockout tests.

Strategy:
  - conftest sets a NoOpLockoutStore globally so other tests are never affected.
  - Each test here uses the `lockout_client` fixture which swaps in a real
    InMemoryLockoutStore for the duration of that test only, then restores
    the NoOp store after.
  - Tests use a unique email per scenario to avoid counter bleed between
    parametrized cases (even though the store is reset per fixture).

What we verify:
  1. Login succeeds normally before any failures
  2. Failed attempts increment the counter (401 on each)
  3. After max_attempts failures, account is locked (401 with lockout message)
  4. Correct password is rejected while account is locked
  5. Successful login resets the counter — subsequent failures start fresh
  6. Non-existent email failures also increment lockout counter (consistent timing)
  7. Lockout is per-email — other accounts are unaffected
  8. Counter resets after the window expires
"""
import asyncio
import time

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app as fastapi_app
from app.lockout import (
    InMemoryLockoutStore,
    NoOpLockoutStore,
    set_lockout_manager,
)
from app.middleware import CSRF_COOKIE_NAME, CSRF_HEADER_NAME

_TEST_CSRF_TOKEN = "test-csrf-token-for-testing"
_MAX_ATTEMPTS = 3   # Use 3 in tests so we don't need to repeat 5 requests everywhere
_WINDOW = 900


@pytest_asyncio.fixture
async def lockout_client(registered_user):
    """
    AsyncClient that uses a REAL InMemoryLockoutStore (threshold=3).
    Restores NoOpLockoutStore after the test completes.
    registered_user fixture ensures a verified user exists.
    """
    real_store = InMemoryLockoutStore(max_attempts=_MAX_ATTEMPTS, window_seconds=_WINDOW)
    set_lockout_manager(real_store)

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test/api/v1",
        headers={CSRF_HEADER_NAME: _TEST_CSRF_TOKEN},
        cookies={
            CSRF_COOKIE_NAME: _TEST_CSRF_TOKEN,
        },
    ) as c:
        yield c, real_store, registered_user

    # Always restore no-op after test
    set_lockout_manager(NoOpLockoutStore())


# ---------------------------------------------------------------------------
# 1. Normal login succeeds before any failures
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_lockout_normal_login_succeeds(lockout_client):
    c, store, user = lockout_client
    c.cookies.set("access_token", f"Bearer {user['token']}")

    res = await c.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert res.status_code == 200
    assert "access_token" in res.json()


# ---------------------------------------------------------------------------
# 2. Failed attempts return 401 and counter increments
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_lockout_wrong_password_increments_counter(lockout_client):
    c, store, user = lockout_client

    # One failure
    res = await c.post(
        "/auth/login",
        json={"email": user["email"], "password": "WrongPassword1!"},
    )
    assert res.status_code == 401

    # Counter should be 1 — not yet locked
    assert not await store.is_locked(user["email"])


@pytest.mark.asyncio
async def test_lockout_multiple_failures_before_threshold(lockout_client):
    c, store, user = lockout_client

    for i in range(_MAX_ATTEMPTS - 1):
        res = await c.post(
            "/auth/login",
            json={"email": user["email"], "password": "WrongPass1!"},
        )
        assert res.status_code == 401

    # Still not locked — one attempt remaining
    assert not await store.is_locked(user["email"])


# ---------------------------------------------------------------------------
# 3. After max_attempts, account is locked
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_lockout_triggers_after_max_attempts(lockout_client):
    c, store, user = lockout_client

    # Exhaust all attempts
    for _ in range(_MAX_ATTEMPTS):
        await c.post(
            "/auth/login",
            json={"email": user["email"], "password": "WrongPass1!"},
        )

    # Now locked
    assert await store.is_locked(user["email"])

    # Next attempt — should be locked out
    res = await c.post(
        "/auth/login",
        json={"email": user["email"], "password": "WrongPass1!"},
    )
    assert res.status_code == 401
    body = res.json()["detail"].lower()
    assert "locked" in body or "too many" in body


# ---------------------------------------------------------------------------
# 4. Correct password rejected while account is locked
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_lockout_correct_password_rejected_while_locked(lockout_client):
    c, store, user = lockout_client

    # Exhaust attempts
    for _ in range(_MAX_ATTEMPTS):
        await c.post(
            "/auth/login",
            json={"email": user["email"], "password": "WrongPass1!"},
        )

    assert await store.is_locked(user["email"])

    # Even correct password is blocked
    res = await c.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert res.status_code == 401
    assert "locked" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 5. Successful login resets the counter
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_lockout_success_resets_counter(lockout_client):
    c, store, user = lockout_client

    # Some failures (below threshold)
    for _ in range(_MAX_ATTEMPTS - 1):
        await c.post(
            "/auth/login",
            json={"email": user["email"], "password": "WrongPass1!"},
        )

    # Successful login resets counter
    res = await c.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert res.status_code == 200
    assert not await store.is_locked(user["email"])

    # New failures start from zero
    for _ in range(_MAX_ATTEMPTS - 1):
        await c.post(
            "/auth/login",
            json={"email": user["email"], "password": "WrongPass1!"},
        )
    assert not await store.is_locked(user["email"])


# ---------------------------------------------------------------------------
# 6. Non-existent email failures also increment (timing consistency)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_lockout_nonexistent_email_increments(lockout_client):
    c, store, user = lockout_client
    ghost_email = "ghost-nobody@example.com"

    for _ in range(_MAX_ATTEMPTS):
        await c.post(
            "/auth/login",
            json={"email": ghost_email, "password": "WrongPass1!"},
        )

    assert await store.is_locked(ghost_email)

    res = await c.post(
        "/auth/login",
        json={"email": ghost_email, "password": "WrongPass1!"},
    )
    assert res.status_code == 401
    assert "locked" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 7. Lockout is per-email — other accounts are unaffected
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_lockout_is_per_email(lockout_client):
    c, store, user = lockout_client

    # Lock the registered user's account
    for _ in range(_MAX_ATTEMPTS):
        await c.post(
            "/auth/login",
            json={"email": user["email"], "password": "WrongPass1!"},
        )
    assert await store.is_locked(user["email"])

    # A completely different email is NOT locked
    assert not await store.is_locked("innocent@example.com")


# ---------------------------------------------------------------------------
# 8. Window expiry resets the counter
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_lockout_window_expiry_resets_counter():
    """
    Use a very short window (1 second) to verify the counter resets
    after the window expires without needing to sleep 15 minutes.
    """
    short_store = InMemoryLockoutStore(max_attempts=2, window_seconds=1)
    email = "expiry-test@example.com"

    await short_store.record_failure(email)
    await short_store.record_failure(email)
    assert await short_store.is_locked(email)

    # Wait for window to expire
    await asyncio.sleep(1.1)

    # Now unlocked — window expired
    assert not await short_store.is_locked(email)

    # Counter also resets — new failures start from 0
    count = await short_store.record_failure(email)
    assert count == 1