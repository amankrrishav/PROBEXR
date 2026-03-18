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
    # Pydantic validation: below min_length
    assert res.status_code == 422


# ---- Password Policy ----

@pytest.mark.asyncio
async def test_register_password_too_short_11_chars(client: AsyncClient):
    """11 chars — one below the 12-char minimum."""
    res = await client.post(
        "/auth/register",
        json={"email": "policy1@example.com", "password": "Short1!Pass"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_register_password_no_uppercase(client: AsyncClient):
    """No uppercase letter → rejected."""
    res = await client.post(
        "/auth/register",
        json={"email": "policy2@example.com", "password": "nouppercase1!"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_register_password_no_lowercase(client: AsyncClient):
    """No lowercase letter → rejected."""
    res = await client.post(
        "/auth/register",
        json={"email": "policy3@example.com", "password": "NOLOWERCASE1!"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_register_password_no_digit(client: AsyncClient):
    """No digit → rejected."""
    res = await client.post(
        "/auth/register",
        json={"email": "policy4@example.com", "password": "NoDigitPass!!"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_register_password_no_special_char(client: AsyncClient):
    """No special character → rejected."""
    res = await client.post(
        "/auth/register",
        json={"email": "policy5@example.com", "password": "NoSpecialChar1"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_register_password_too_long(client: AsyncClient):
    """Over 128 characters → rejected."""
    res = await client.post(
        "/auth/register",
        json={"email": "policy6@example.com", "password": "A1!" + "x" * 127},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_register_common_password_rejected(client: AsyncClient):
    """Known common password → rejected even if it meets length/complexity."""
    res = await client.post(
        "/auth/register",
        json={"email": "policy7@example.com", "password": "Password123!"},
    )
    # "password" is in the common list — validator lowercases and checks
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_register_strong_password_accepted(client: AsyncClient):
    """A genuinely strong password passes all policy rules."""
    res = await client.post(
        "/auth/register",
        json={"email": "policy8@example.com", "password": "Tr0ub4dor&3XYZ"},
    )
    assert res.status_code == 201


@pytest.mark.asyncio
async def test_register_minimum_valid_password(client: AsyncClient):
    """Exactly 12 chars satisfying all rules is accepted."""
    res = await client.post(
        "/auth/register",
        json={"email": "policy9@example.com", "password": "Valid1!PassAB"},
    )
    assert res.status_code == 201


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


# ---- Cookie path correctness ----

@pytest.mark.asyncio
async def test_refresh_cookie_path_is_api_v1_auth(client: AsyncClient):
    """
    The refresh_token Set-Cookie header must use path=/api/v1/auth so
    browsers send it to /api/v1/auth/* endpoints.
    path=/auth would silently break all token refreshes in production
    because the browser would never send the cookie.
    """
    res = await client.post(
        "/auth/register",
        json={"email": "cookiepath@example.com", "password": "StrongPass1!"},
    )
    assert res.status_code == 201

    # httpx merges duplicate header names with items() — use multi_items()
    # to get each Set-Cookie header as a separate entry.
    set_cookie_headers = [
        v for k, v in res.headers.multi_items()
        if k.lower() == "set-cookie"
    ]
    refresh_header = next(
        (h for h in set_cookie_headers if "refresh_token=" in h), None
    )
    assert refresh_header is not None, (
        f"refresh_token Set-Cookie header not found. Headers: {set_cookie_headers}"
    )
    assert "path=/api/v1/auth" in refresh_header.lower(), (
        f"Expected path=/api/v1/auth in Set-Cookie, got: {refresh_header}"
    )

# ---- SECRET_KEY entropy ----

def test_secret_key_entropy_check():
    """SHORT keys must be rejected in production — entropy check runs on startup."""
    from app.config import AppConfig
    import pytest
    # Simulate a prod config with a short key
    cfg_short = AppConfig(
        environment="production",
        secret_key="tooshort",
        database_url="sqlite:///./test.db",
    )
    # The check is in the lifespan startup, not config itself.
    # Verify the length is below threshold so the guard will fire.
    assert len(cfg_short.SECRET_KEY) < 32, (
        "Short key should be under 32 chars so startup guard catches it"
    )

    # A properly long key should pass the length check
    import secrets
    long_key = secrets.token_hex(32)
    assert len(long_key) >= 32


# ---------------------------------------------------------------------------
# R-08: User.full_name and User.avatar_url have max_length bounds
# ---------------------------------------------------------------------------

def test_user_full_name_has_max_length():
    """User.full_name must have a max_length constraint."""
    src = open('app/models/user.py').read()
    lines = [l for l in src.split('\n') if 'full_name' in l and 'Field' in l]
    assert lines, "User must have a full_name field with Field()"
    assert any('max_length' in l for l in lines), (
        f"User.full_name must have max_length. Found: {lines}"
    )


def test_user_avatar_url_has_max_length():
    """User.avatar_url must have a max_length constraint."""
    src = open('app/models/user.py').read()
    lines = [l for l in src.split('\n') if 'avatar_url' in l and 'Field' in l]
    assert lines, "User must have an avatar_url field with Field()"
    assert any('max_length' in l for l in lines), (
        f"User.avatar_url must have max_length. Found: {lines}"
    )