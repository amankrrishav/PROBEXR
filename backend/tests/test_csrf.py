"""
test_csrf.py — Tests for CSRFMiddleware dual-submit cookie protection.

Strategy:
  - `csrf_client`: a plain AsyncClient with NO CSRF cookie/header — used to
    verify that mutating requests are blocked.
  - `client` (from conftest): already has matching csrf_token cookie + header,
    so it passes CSRF and tests normal auth behaviour.

What we verify:
  1. POST with no cookie AND no header → 403 "missing"
  2. POST with cookie only (no header) → 403 "missing"
  3. POST with header only (no cookie) → 403 "missing"
  4. POST with mismatched cookie/header → 403 "mismatch"
  5. POST with valid matching pair → NOT a CSRF 403 (may be 401/400/422 from
     the actual route — but not a CSRF block)
  6. GET without any CSRF → always allowed (safe method)
  7. OPTIONS without any CSRF → always allowed
  8. Exempt POST paths bypass CSRF check (OAuth callbacks)
  9. Every response sets a csrf_token cookie that is readable by JS (not httponly)
 10. csrf_token cookie is refreshed on GET responses too
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app as fastapi_app
from app.middleware import CSRF_COOKIE_NAME, CSRF_HEADER_NAME


# ---------------------------------------------------------------------------
# Fixtures: clients with different CSRF setups
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def csrf_client():
    """Plain client — no CSRF cookie, no CSRF header."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test/api/v1",
    ) as c:
        yield c


@pytest_asyncio.fixture
async def csrf_cookie_only_client():
    """Client with csrf_token cookie but no X-CSRF-Token header."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test/api/v1",
        cookies={CSRF_COOKIE_NAME: "valid-token-abc123"},
    ) as c:
        yield c


@pytest_asyncio.fixture
async def csrf_header_only_client():
    """Client with X-CSRF-Token header but no csrf_token cookie."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test/api/v1",
        headers={CSRF_HEADER_NAME: "valid-token-abc123"},
    ) as c:
        yield c


@pytest_asyncio.fixture
async def csrf_mismatch_client():
    """Client with cookie and header that do NOT match."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test/api/v1",
        cookies={CSRF_COOKIE_NAME: "token-from-cookie"},
        headers={CSRF_HEADER_NAME: "different-token-in-header"},
    ) as c:
        yield c


@pytest_asyncio.fixture
async def csrf_valid_client():
    """Client with matching csrf_token cookie and X-CSRF-Token header."""
    token = "matching-csrf-token-xyz"
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test/api/v1",
        cookies={CSRF_COOKIE_NAME: token},
        headers={CSRF_HEADER_NAME: token},
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# 1. POST blocked — no cookie, no header
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_csrf_post_no_token_blocked(csrf_client: AsyncClient):
    """POST with no CSRF cookie or header is blocked with 403."""
    res = await csrf_client.post(
        "/auth/login",
        json={"email": "x@example.com", "password": "password123"},
    )
    assert res.status_code == 403
    assert "csrf" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_csrf_post_no_token_message_says_missing(csrf_client: AsyncClient):
    """403 detail message says 'missing'."""
    res = await csrf_client.post(
        "/auth/register",
        json={"email": "x@example.com", "password": "password123"},
    )
    assert res.status_code == 403
    assert "missing" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 2. POST blocked — cookie only, no header
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_csrf_post_cookie_only_blocked(csrf_cookie_only_client: AsyncClient):
    """POST with csrf_token cookie but no X-CSRF-Token header is blocked."""
    res = await csrf_cookie_only_client.post(
        "/auth/login",
        json={"email": "x@example.com", "password": "password123"},
    )
    assert res.status_code == 403
    assert "missing" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 3. POST blocked — header only, no cookie
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_csrf_post_header_only_blocked(csrf_header_only_client: AsyncClient):
    """POST with X-CSRF-Token header but no csrf_token cookie is blocked."""
    res = await csrf_header_only_client.post(
        "/auth/login",
        json={"email": "x@example.com", "password": "password123"},
    )
    assert res.status_code == 403
    assert "missing" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 4. POST blocked — cookie/header mismatch
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_csrf_post_mismatch_blocked(csrf_mismatch_client: AsyncClient):
    """POST where cookie and header don't match returns 403 mismatch."""
    res = await csrf_mismatch_client.post(
        "/auth/login",
        json={"email": "x@example.com", "password": "password123"},
    )
    assert res.status_code == 403
    assert "mismatch" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_csrf_put_mismatch_blocked(csrf_mismatch_client: AsyncClient):
    """PUT with mismatched tokens is also blocked."""
    res = await csrf_mismatch_client.put(
        "/auth/me",
        json={"full_name": "Test"},
    )
    assert res.status_code == 403
    assert "mismatch" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_csrf_delete_mismatch_blocked(csrf_mismatch_client: AsyncClient):
    """DELETE with mismatched tokens is also blocked."""
    res = await csrf_mismatch_client.delete("/documents/1")
    assert res.status_code == 403
    assert "mismatch" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 5. POST passes CSRF with valid matching pair (route handles it from there)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_csrf_post_valid_pair_not_blocked(csrf_valid_client: AsyncClient):
    """Valid matching cookie+header passes CSRF — route returns 401 (not 403)."""
    res = await csrf_valid_client.post(
        "/auth/login",
        json={"email": "x@example.com", "password": "password123"},
    )
    # CSRF passed — now the actual auth logic runs and returns 401 (bad creds)
    # NOT a 403 CSRF block
    assert res.status_code != 403
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_csrf_post_valid_pair_register_not_blocked(csrf_valid_client: AsyncClient):
    """Valid CSRF pair on register — gets 201 or 400 (not 403)."""
    res = await csrf_valid_client.post(
        "/auth/register",
        json={"email": "newuser@example.com", "password": "StrongPass1!"},
    )
    assert res.status_code != 403
    assert res.status_code in (201, 400)


# ---------------------------------------------------------------------------
# 6. GET is always allowed — no CSRF check
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_csrf_get_never_blocked(csrf_client: AsyncClient):
    """GET without any CSRF tokens is never blocked by CSRF middleware."""
    res = await csrf_client.get("/")
    # Health is public — should return 200, not 403
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_csrf_get_auth_me_not_csrf_blocked(csrf_client: AsyncClient):
    """GET /auth/me without CSRF — blocked by auth (401), not CSRF (403)."""
    res = await csrf_client.get("/auth/me")
    assert res.status_code == 401  # auth blocks it, not CSRF


# ---------------------------------------------------------------------------
# 7. OPTIONS is always allowed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_csrf_options_never_blocked(csrf_client: AsyncClient):
    """OPTIONS (preflight) is always safe — never CSRF-blocked."""
    res = await csrf_client.options("/auth/login")
    # May be 200 or 405 depending on route — but NOT 403 from CSRF
    assert res.status_code != 403


# ---------------------------------------------------------------------------
# 8. Exempt paths bypass CSRF check
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_csrf_exempt_google_callback(csrf_client: AsyncClient):
    """Google OAuth callback is CSRF-exempt — no 403 from CSRF."""
    res = await csrf_client.post(
        "/auth/google/callback",
        json={"code": "fakecode", "state": "fakestate"},
    )
    # Should get 400 (bad state/code) — not 403 CSRF
    assert res.status_code != 403
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_csrf_exempt_github_callback(csrf_client: AsyncClient):
    """GitHub OAuth callback is CSRF-exempt — no 403 from CSRF."""
    res = await csrf_client.post(
        "/auth/github/callback",
        json={"code": "fakecode", "state": "fakestate"},
    )
    assert res.status_code != 403
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# 9 & 10. Every response sets csrf_token cookie — readable by JS (not httponly)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_csrf_cookie_set_on_get_response(csrf_client: AsyncClient):
    """Every GET response sets a csrf_token cookie."""
    res = await csrf_client.get("/")
    assert CSRF_COOKIE_NAME in res.cookies


@pytest.mark.asyncio
async def test_csrf_cookie_set_on_blocked_post(csrf_client: AsyncClient):
    """Even a blocked 403 POST response still sets the csrf_token cookie
    so the frontend can retry with the correct token."""
    res = await csrf_client.post(
        "/auth/login",
        json={"email": "x@example.com", "password": "pass"},
    )
    assert res.status_code == 403
    assert CSRF_COOKIE_NAME in res.cookies


@pytest.mark.asyncio
async def test_csrf_cookie_not_httponly(csrf_client: AsyncClient):
    """csrf_token cookie must NOT be httponly — JS needs to read it."""
    res = await csrf_client.get("/")
    assert CSRF_COOKIE_NAME in res.cookies
    # httpx exposes Set-Cookie headers — check that HttpOnly is absent
    set_cookie_headers = res.headers.get_list("set-cookie") if hasattr(res.headers, "get_list") else [
        v for k, v in res.headers.items() if k.lower() == "set-cookie"
    ]
    csrf_cookie_header = next(
        (h for h in set_cookie_headers if CSRF_COOKIE_NAME in h), None
    )
    assert csrf_cookie_header is not None, "csrf_token Set-Cookie header not found"
    assert "httponly" not in csrf_cookie_header.lower(), (
        "csrf_token must NOT be HttpOnly — JS needs to read it for dual-submit"
    )


@pytest.mark.asyncio
async def test_csrf_cookie_refreshed_on_valid_request(csrf_valid_client: AsyncClient):
    """On a valid passing request, the csrf_token cookie is refreshed in the response."""
    res = await csrf_valid_client.get("/auth/me")
    # Auth will return 401 but CSRF still processes and sets cookie
    assert CSRF_COOKIE_NAME in res.cookies


@pytest.mark.asyncio
async def test_csrf_existing_cookie_value_preserved(csrf_client: AsyncClient):
    """If csrf_token cookie already exists on request, same value is echoed back."""
    existing_token = "my-existing-csrf-token-999"
    res = await csrf_client.get("/", cookies={CSRF_COOKIE_NAME: existing_token})
    assert CSRF_COOKIE_NAME in res.cookies
    assert res.cookies[CSRF_COOKIE_NAME] == existing_token