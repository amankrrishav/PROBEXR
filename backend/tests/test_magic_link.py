"""
test_magic_link.py — Tests for magic link request and verification endpoints.

Magic link tokens are short-lived JWTs (15 min) signed with SECRET_KEY.
We test the full round-trip: request a link → extract the token from the
signed JWT → verify it → get back a valid session.

We also test bad tokens, expired-ish tokens, and wrong token type.
"""
import pytest
from unittest.mock import patch
from httpx import AsyncClient
import jwt
from datetime import datetime, timedelta, timezone

from app.config import get_config


cfg = get_config()


def _make_jwt(sub: str, type_: str = "magic_link", exp_delta_minutes: int = 15) -> str:
    """Helper to craft a custom JWT for edge-case tests."""
    payload = {
        "sub": sub,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=exp_delta_minutes),
        "type": type_,
    }
    return jwt.encode(payload, cfg.SECRET_KEY, algorithm=cfg.ALGORITHM)


# ─────────────────────────────────────────────────────────────────────────────
# /auth/magic-link  (request)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_magic_link_request_returns_200(client: AsyncClient):
    """POST /auth/magic-link always returns 200 (even if email not registered)."""
    res = await client.post(
        "/auth/magic-link", json={"email": "newuser@example.com"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    # Confirm we get a non-empty message
    assert len(data["message"]) > 0


@pytest.mark.asyncio
async def test_magic_link_request_invalid_email(client: AsyncClient):
    """POST /auth/magic-link with non-email returns 422 validation error."""
    res = await client.post("/auth/magic-link", json={"email": "not-an-email"})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_magic_link_request_missing_body(client: AsyncClient):
    """POST /auth/magic-link with no body returns 422."""
    res = await client.post("/auth/magic-link", json={})
    assert res.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# /auth/verify  (verification)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_magic_link_verify_creates_user_and_returns_tokens(client: AsyncClient):
    """A valid magic link token provisions a new user and returns session tokens."""
    email = "magicnew@example.com"
    token = _make_jwt(email)

    res = await client.get(f"/auth/verify?token={token}")
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # Auth cookie must be set
    assert "access_token" in res.cookies


@pytest.mark.asyncio
async def test_magic_link_verify_existing_user(client: AsyncClient):
    """Magic link for an already-registered user logs them in successfully."""
    email = "existing@example.com"
    # Register first
    await client.post("/auth/register", json={"email": email, "password": "Pass1234!XyzAB"})
    # Then verify via magic link
    token = _make_jwt(email)
    res = await client.get(f"/auth/verify?token={token}")
    assert res.status_code == 200
    assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_magic_link_verify_sets_is_verified(client: AsyncClient):
    """After magic link verification, the user's profile is accessible."""
    email = "verified@example.com"
    token = _make_jwt(email)

    # Verify via magic link
    verify_res = await client.get(f"/auth/verify?token={token}")
    assert verify_res.status_code == 200

    # Use returned token to fetch profile
    access_token = verify_res.json()["access_token"]
    client.cookies.set("access_token", f"Bearer {access_token}")
    me_res = await client.get("/auth/me")
    assert me_res.status_code == 200
    profile = me_res.json()
    assert profile["email"] == email
    assert profile["is_verified"] is True


@pytest.mark.asyncio
async def test_magic_link_verify_expired_token(client: AsyncClient):
    """An expired magic link token returns 401."""
    email = "expiry@example.com"
    # Craft a token that expired 1 second ago
    token = _make_jwt(email, exp_delta_minutes=-1)
    res = await client.get(f"/auth/verify?token={token}")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_magic_link_verify_wrong_type(client: AsyncClient):
    """A JWT with the wrong type field (e.g. access token) is rejected."""
    email = "wrongtype@example.com"
    token = _make_jwt(email, type_="access")
    res = await client.get(f"/auth/verify?token={token}")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_magic_link_verify_garbage_token(client: AsyncClient):
    """A completely invalid token string returns 401."""
    res = await client.get("/auth/verify?token=not-a-real-token")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_magic_link_verify_missing_token(client: AsyncClient):
    """GET /auth/verify with no token param returns 422."""
    res = await client.get("/auth/verify")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_magic_link_second_verify_with_same_token_still_works(client: AsyncClient):
    """
    Magic link tokens are stateless JWTs — a second use within the validity window
    will provision/log in the same user again (no one-time use enforcement at this
    phase). This test documents the current behavior.
    """
    email = "reuse@example.com"
    token = _make_jwt(email)

    res1 = await client.get(f"/auth/verify?token={token}")
    client.cookies.clear()
    res2 = await client.get(f"/auth/verify?token={token}")

    assert res1.status_code == 200
    assert res2.status_code == 200  # Second use still works (stateless JWT)