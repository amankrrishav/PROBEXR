"""
test_social_auth.py — Tests for Google/GitHub OAuth callback endpoints.

Strategy: we patch at the ROUTER's import site (app.routers.auth.*) so the
mock intercepts the call inside the route handler, not at the service layer.
This means tests never hit external APIs.

The OAuth state CSRF parameter is generated via conftest.make_oauth_state()
and set as both a cookie and JSON body field to satisfy the validation.
"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from tests.conftest import make_oauth_state


# ─────────────────────────────────────────────────────────────────────────────
# Fake user info payloads
# ─────────────────────────────────────────────────────────────────────────────

GOOGLE_USER = {
    "sub": "google-uid-123",
    "id": "google-uid-123",
    "email": "alice@gmail.com",
    "name": "Alice G",
    "picture": "https://example.com/alice.jpg",
}

GITHUB_USER = {
    "id": 9001,
    "email": "bob@github.com",
    "name": "Bob H",
    "login": "bobh",
    "avatar_url": "https://example.com/bob.jpg",
}

# Patch targets — must match where the names are imported in the router
_GOOGLE_PATCH = "app.routers.auth.get_google_user_info"
_GITHUB_PATCH = "app.routers.auth.get_github_user_info"


def _oauth_state_for(provider: str, client: AsyncClient) -> dict:
    """Generate a valid state token and set the cookie on the client."""
    state = make_oauth_state(provider)
    client.cookies.set("oauth_state", state)
    return {"state": state}


# ─────────────────────────────────────────────────────────────────────────────
# Google OAuth
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_google_callback_creates_new_user(client: AsyncClient):
    """First-time Google login creates a new user and returns tokens."""
    extra = _oauth_state_for("google", client)
    with patch(_GOOGLE_PATCH, new=AsyncMock(return_value=GOOGLE_USER)):
        res = await client.post("/auth/google/callback", json={"code": "fake-code", **extra})

    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "access_token" in res.cookies


@pytest.mark.asyncio
async def test_google_callback_returns_existing_user(client: AsyncClient):
    """Second Google login with same sub reuses the existing user."""
    with patch(_GOOGLE_PATCH, new=AsyncMock(return_value=GOOGLE_USER)):
        extra = _oauth_state_for("google", client)
        res1 = await client.post("/auth/google/callback", json={"code": "fake-code", **extra})
        client.cookies.clear()
        extra = _oauth_state_for("google", client)
        res2 = await client.post("/auth/google/callback", json={"code": "fake-code", **extra})

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert "access_token" in res2.json()


@pytest.mark.asyncio
async def test_google_callback_missing_code(client: AsyncClient):
    """Callback with no code returns 400."""
    extra = _oauth_state_for("google", client)
    res = await client.post("/auth/google/callback", json={**extra})
    assert res.status_code == 400
    assert "Code missing" in res.json()["detail"]


@pytest.mark.asyncio
async def test_google_callback_provider_error(client: AsyncClient):
    """If the social service raises, we return 400."""
    extra = _oauth_state_for("google", client)
    with patch(_GOOGLE_PATCH, new=AsyncMock(side_effect=Exception("Token exchange failed"))):
        res = await client.post("/auth/google/callback", json={"code": "bad-code", **extra})

    assert res.status_code == 400
    assert "Token exchange failed" in res.json()["detail"]


@pytest.mark.asyncio
async def test_google_callback_missing_state(client: AsyncClient):
    """Callback without OAuth state returns 400 (CSRF protection)."""
    with patch(_GOOGLE_PATCH, new=AsyncMock(return_value=GOOGLE_USER)):
        res = await client.post("/auth/google/callback", json={"code": "fake-code"})
    assert res.status_code == 400
    assert "state" in res.json()["detail"].lower() or "CSRF" in res.json()["detail"]


@pytest.mark.asyncio
async def test_google_login_redirect(client: AsyncClient):
    """GET /auth/google/login returns a redirect to accounts.google.com."""
    res = await client.get("/auth/google/login", follow_redirects=False)
    assert res.status_code in (302, 307)
    location = res.headers.get("location", "")
    assert "accounts.google.com" in location


# ─────────────────────────────────────────────────────────────────────────────
# GitHub OAuth
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_github_callback_creates_new_user(client: AsyncClient):
    """First-time GitHub login creates a new user and returns tokens."""
    extra = _oauth_state_for("github", client)
    with patch(_GITHUB_PATCH, new=AsyncMock(return_value=GITHUB_USER)):
        res = await client.post("/auth/github/callback", json={"code": "fake-code", **extra})

    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert "access_token" in res.cookies


@pytest.mark.asyncio
async def test_github_callback_returns_existing_user(client: AsyncClient):
    """Second GitHub login with same id reuses the existing user."""
    with patch(_GITHUB_PATCH, new=AsyncMock(return_value=GITHUB_USER)):
        extra = _oauth_state_for("github", client)
        res1 = await client.post("/auth/github/callback", json={"code": "fake-code", **extra})
        client.cookies.clear()
        extra = _oauth_state_for("github", client)
        res2 = await client.post("/auth/github/callback", json={"code": "fake-code", **extra})

    assert res1.status_code == 200
    assert res2.status_code == 200


@pytest.mark.asyncio
async def test_github_callback_missing_code(client: AsyncClient):
    """Callback with no code returns 400."""
    extra = _oauth_state_for("github", client)
    res = await client.post("/auth/github/callback", json={**extra})
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_github_callback_provider_error(client: AsyncClient):
    """If the social service raises, we return 400."""
    extra = _oauth_state_for("github", client)
    with patch(_GITHUB_PATCH, new=AsyncMock(side_effect=Exception("Bad credentials"))):
        res = await client.post("/auth/github/callback", json={"code": "bad-code", **extra})

    assert res.status_code == 400


@pytest.mark.asyncio
async def test_github_login_redirect(client: AsyncClient):
    """GET /auth/github/login returns a redirect to github.com."""
    res = await client.get("/auth/github/login", follow_redirects=False)
    assert res.status_code in (302, 307)
    location = res.headers.get("location", "")
    assert "github.com" in location


# ─────────────────────────────────────────────────────────────────────────────
# Account Linking — same email, different provider
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_social_links_to_existing_email_account(client: AsyncClient):
    """Social login with an email that already has an email/password account links them."""
    email = "shared@example.com"
    await client.post("/auth/register", json={"email": email, "password": "Pass1234!XyzAB"})
    client.cookies.clear()

    google_profile = {**GOOGLE_USER, "email": email}
    extra = _oauth_state_for("google", client)
    with patch(_GOOGLE_PATCH, new=AsyncMock(return_value=google_profile)):
        res = await client.post("/auth/google/callback", json={"code": "link-code", **extra})

    assert res.status_code == 200
    assert "access_token" in res.json()