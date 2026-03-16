"""
Auth smoke tests — register, login, /me, logout, refresh, token revocation.
"""
import pytest
from httpx import AsyncClient


# ---- Registration ----

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    res = await client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "StrongPass1!"},
    )
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    # Both cookies should be set
    assert "access_token" in res.cookies
    assert "refresh_token" in res.cookies


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "StrongPass1!"}
    res1 = await client.post("/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/auth/register", json=payload)

    # Email enumeration defense: duplicate registration must NOT return 400
    # with a message that reveals the email is taken. It returns 200 with a
    # generic message — caller cannot distinguish new vs existing email.
    assert res2.status_code == 200
    body = res2.json()
    assert "already registered" not in str(body).lower()
    assert "message" in body
    # No tokens — caller is not logged in automatically on a duplicate attempt
    assert "access_token" not in body
    assert "refresh_token" not in body


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    res = await client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "abc"},
    )
    # Pydantic validation: min_length=8
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    res = await client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "StrongPass1!"},
    )
    assert res.status_code == 422


# ---- Login ----

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, registered_user: dict):
    res = await client.post(
        "/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "refresh_token" in res.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, registered_user: dict):
    res = await client.post(
        "/auth/login",
        json={"email": registered_user["email"], "password": "WrongPassword!"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    res = await client.post(
        "/auth/login",
        json={"email": "ghost@example.com", "password": "Whatever123!"},
    )
    assert res.status_code == 401


# ---- /me ----

@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient, registered_user: dict):
    client.cookies.set("access_token", f"Bearer {registered_user['token']}")
    res = await client.get("/auth/me")
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == registered_user["email"]
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    res = await client.get("/auth/me")
    assert res.status_code == 401


# ---- Refresh ----

@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient, registered_user: dict):
    """Valid refresh token returns new access + refresh tokens."""
    client.cookies.set("refresh_token", registered_user["refresh_token"])
    res = await client.post("/auth/refresh")
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # New refresh token should be different from the old one
    assert data["refresh_token"] != registered_user["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_rotates_token(client: AsyncClient, registered_user: dict):
    """After refresh, old token is revoked and cannot be reused."""
    old_refresh = registered_user["refresh_token"]
    client.cookies.set("refresh_token", old_refresh)

    # First refresh should succeed
    res1 = await client.post("/auth/refresh")
    assert res1.status_code == 200
    new_refresh = res1.json()["refresh_token"]

    # Reuse old token — should fail (reuse detection)
    client.cookies.set("refresh_token", old_refresh)
    res2 = await client.post("/auth/refresh")
    assert res2.status_code == 401
    assert "reuse" in res2.json()["detail"].lower()

    # Even the new token should be revoked now (family revocation)
    client.cookies.set("refresh_token", new_refresh)
    res3 = await client.post("/auth/refresh")
    assert res3.status_code == 401


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    """Random token string returns 401."""
    client.cookies.set("refresh_token", "not-a-real-token")
    res = await client.post("/auth/refresh")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_refresh_no_cookie(client: AsyncClient):
    """No refresh token cookie returns 401."""
    res = await client.post("/auth/refresh")
    assert res.status_code == 401


# ---- Logout ----

@pytest.mark.asyncio
async def test_logout(client: AsyncClient, registered_user: dict):
    client.cookies.set("access_token", f"Bearer {registered_user['token']}")
    client.cookies.set("refresh_token", registered_user["refresh_token"])
    res = await client.post("/auth/logout")
    assert res.status_code == 200
    assert "logged out" in res.json()["message"].lower()

    # Refresh token should be revoked
    client.cookies.set("refresh_token", registered_user["refresh_token"])
    res2 = await client.post("/auth/refresh")
    assert res2.status_code == 401


# ---- Logout All ----

@pytest.mark.asyncio
async def test_logout_all(client: AsyncClient, registered_user: dict):
    """Logout-all revokes all refresh tokens for the user."""
    # Login a second time to create a second refresh token
    login_res = await client.post(
        "/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    second_refresh = login_res.json()["refresh_token"]

    # Call logout-all with auth
    client.cookies.set("access_token", f"Bearer {registered_user['token']}")
    res = await client.post("/auth/logout-all")
    assert res.status_code == 200
    assert "tokens revoked" in res.json()["message"].lower()

    # Both refresh tokens should be revoked
    client.cookies.set("refresh_token", registered_user["refresh_token"])
    assert (await client.post("/auth/refresh")).status_code == 401

    client.cookies.set("refresh_token", second_refresh)
    assert (await client.post("/auth/refresh")).status_code == 401