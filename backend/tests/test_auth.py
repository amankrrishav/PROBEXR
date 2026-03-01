"""
Auth smoke tests — register, login, /me, logout.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    res = await client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "StrongPass1!"},
    )
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # Cookie should be set
    assert "access_token" in res.cookies


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "StrongPass1!"}
    res1 = await client.post("/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already registered" in res2.json()["detail"].lower()


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


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, registered_user: dict):
    res = await client.post(
        "/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data


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


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, registered_user: dict):
    client.cookies.set("access_token", f"Bearer {registered_user['token']}")
    res = await client.post("/auth/logout")
    assert res.status_code == 200
    assert "logged out" in res.json()["message"].lower()
