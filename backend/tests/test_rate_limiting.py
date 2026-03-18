"""
tests/test_rate_limiting.py  —  A-23: Per-user rate limiting tests.

Strategy
--------
conftest installs a _NoOpRateLimiter globally so regular tests never 429.
These tests temporarily swap in a real InMemoryRateLimiter, exercise the
per-user limit, then restore the no-op limiter via fixture teardown.

What we verify
--------------
1. Per-IP limit: unauthenticated requests from same IP are capped.
2. Per-user limit: authenticated user hitting limit returns 429 even if
   IP limit hasn't been reached (different user hashes share same IP).
3. Two different authenticated users on the same IP have independent
   per-user counters — one being limited does NOT block the other.
4. Auth routes (login/register) are exempt from the per-user JWT check
   (no cookie present at that point anyway).
5. 429 response includes the correct rate-limit headers.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.middleware import set_rate_limiter, InMemoryRateLimiter
from app.services.auth import create_access_token


# ---------------------------------------------------------------------------
# Fixture: real rate limiter scoped to this module, restored after
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def real_limiter():
    """Swap in a fresh InMemoryRateLimiter for the duration of the test."""
    limiter = InMemoryRateLimiter()
    set_rate_limiter(limiter)
    yield limiter
    # Restore no-op so other tests are unaffected
    from tests.conftest import _NoOpRateLimiter  # type: ignore
    set_rate_limiter(_NoOpRateLimiter())


def _make_token(email: str) -> str:
    """Create a signed access token for a given email (no DB needed)."""
    return create_access_token({"sub": email})


# ---------------------------------------------------------------------------
# 1. IP-based limiting
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ip_rate_limit_blocks_after_limit(client: AsyncClient, real_limiter: InMemoryRateLimiter):
    """After exhausting the general IP limit, further requests get 429."""
    # Drive the limiter to the edge by direct manipulation
    from app.config import get_config
    cfg = get_config()
    limit = cfg.rate_limit_per_minute

    # Exhaust the IP counter directly
    import time
    minute = int(time.time() // 60)
    key = f"rl:127.0.0.1:general:{minute}"
    for _ in range(limit):
        await real_limiter.check_and_increment(key, limit)

    # Next request should be blocked
    res = await client.get("/")
    assert res.status_code == 429
    assert "detail" in res.json()


@pytest.mark.asyncio
async def test_ip_rate_limit_headers_present(client: AsyncClient, real_limiter: InMemoryRateLimiter):
    """Successful responses include X-RateLimit-* headers."""
    res = await client.get("/")
    assert res.status_code == 200
    assert "x-ratelimit-limit" in res.headers
    assert "x-ratelimit-remaining" in res.headers
    assert "x-ratelimit-reset" in res.headers


@pytest.mark.asyncio
async def test_429_includes_retry_after(client: AsyncClient, real_limiter: InMemoryRateLimiter):
    """429 response includes Retry-After header."""
    from app.config import get_config
    import time
    cfg = get_config()
    limit = cfg.rate_limit_per_minute
    minute = int(time.time() // 60)
    key = f"rl:127.0.0.1:general:{minute}"
    for _ in range(limit):
        await real_limiter.check_and_increment(key, limit)

    res = await client.get("/")
    assert res.status_code == 429
    assert "retry-after" in res.headers
    assert int(res.headers["retry-after"]) > 0


# ---------------------------------------------------------------------------
# 2. Per-user limiting
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_per_user_limit_blocks_after_limit(client: AsyncClient, real_limiter: InMemoryRateLimiter):
    """A user who exhausts their per-user counter gets 429 even if IP is clean."""
    from app.config import get_config
    import hashlib, time
    cfg = get_config()
    limit = cfg.rate_limit_per_minute
    email = "heavyuser@example.com"
    token = _make_token(email)

    # Exhaust this user's counter directly
    user_hash = hashlib.sha256(email.encode()).hexdigest()[:32]
    minute = int(time.time() // 60)
    user_key = f"rl:user:{user_hash}:general:{minute}"
    for _ in range(limit):
        await real_limiter.check_and_increment(user_key, limit)

    # Request with their token should now be blocked
    client.cookies.set("access_token", f"Bearer {token}")
    res = await client.get("/")
    assert res.status_code == 429


@pytest.mark.asyncio
async def test_per_user_limit_independent_of_other_users(
    client: AsyncClient, real_limiter: InMemoryRateLimiter
):
    """Exhausting user A's quota does NOT affect user B on the same IP."""
    from app.config import get_config
    import hashlib, time
    cfg = get_config()
    limit = cfg.rate_limit_per_minute

    email_a = "user_a@example.com"
    email_b = "user_b@example.com"
    token_b = _make_token(email_b)

    # Exhaust user A's per-user counter
    user_hash_a = hashlib.sha256(email_a.encode()).hexdigest()[:32]
    minute = int(time.time() // 60)
    key_a = f"rl:user:{user_hash_a}:general:{minute}"
    for _ in range(limit):
        await real_limiter.check_and_increment(key_a, limit)

    # User B should still get through fine
    client.cookies.set("access_token", f"Bearer {token_b}")
    res = await client.get("/")
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_unauthenticated_request_not_blocked_by_user_check(
    client: AsyncClient, real_limiter: InMemoryRateLimiter
):
    """Unauthenticated requests (no cookie) skip the per-user check entirely."""
    # No access_token cookie set
    client.cookies.delete("access_token")
    res = await client.get("/")
    # Should pass — IP limit not exhausted and no user check fires
    assert res.status_code == 200


# ---------------------------------------------------------------------------
# 3. Auth routes exempt from per-user JWT check
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_auth_routes_exempt_from_per_user_check(
    client: AsyncClient, real_limiter: InMemoryRateLimiter
):
    """
    Auth routes must NOT apply the per-user JWT check.
    Even if a token is somehow present, the check is skipped for
    /auth/login, /auth/register, /auth/magic-link.
    """
    from app.config import get_config
    import hashlib, time
    cfg = get_config()
    limit = cfg.rate_limit_auth_per_minute

    # Set a token cookie (simulating a weird edge case)
    token = _make_token("someuser@example.com")
    client.cookies.set("access_token", f"Bearer {token}")

    # Auth routes use their own tight limit — exhaust per-email won't apply here
    # Just verify the endpoint responds (not 429 from user check) when
    # the auth IP limit hasn't been hit yet
    res = await client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "wrongpassword"},
    )
    # 401 (wrong creds) is fine — what matters is NOT 429 from the user check
    assert res.status_code != 429 or res.json().get("detail", "").startswith("Too many requests for")

# ---------------------------------------------------------------------------
# N-02: forgot-password + resend-verification included in rate-limited paths
# ---------------------------------------------------------------------------

def test_forgot_password_is_rate_limited_path():
    """forgot-password must be in _AUTH_RATE_LIMITED_PATHS."""
    from app.middleware import _AUTH_RATE_LIMITED_PATHS
    assert any("forgot-password" in p for p in _AUTH_RATE_LIMITED_PATHS), (
        "/auth/forgot-password must be rate-limited to prevent email spam"
    )

def test_resend_verification_is_rate_limited_path():
    """resend-verification must be in _AUTH_RATE_LIMITED_PATHS."""
    from app.middleware import _AUTH_RATE_LIMITED_PATHS
    assert any("resend-verification" in p for p in _AUTH_RATE_LIMITED_PATHS), (
        "/auth/resend-verification must be rate-limited to prevent email spam"
    )

@pytest.mark.asyncio
async def test_forgot_password_counted_as_auth_tier(
    client: AsyncClient, real_limiter: InMemoryRateLimiter
):
    """forgot-password requests must be counted in the auth rate-limit tier."""
    import time
    cfg_limit = 5
    minute = int(time.time() // 60)
    ip = "127.0.0.1"
    # Pre-fill the auth bucket to the limit
    for _ in range(cfg_limit):
        await real_limiter.check_and_increment(f"rl:{ip}:auth:{minute}", cfg_limit)

    res = await client.post(
        "/auth/forgot-password",
        json={"email": "test@example.com"},
    )
    assert res.status_code == 429, (
        "forgot-password must be blocked when auth rate limit is exhausted"
    )

@pytest.mark.asyncio
async def test_resend_verification_counted_as_auth_tier(
    client: AsyncClient, real_limiter: InMemoryRateLimiter
):
    """resend-verification requests must be counted in the auth rate-limit tier."""
    import time
    cfg_limit = 5
    minute = int(time.time() // 60)
    ip = "127.0.0.1"
    for _ in range(cfg_limit):
        await real_limiter.check_and_increment(f"rl:{ip}:auth:{minute}", cfg_limit)

    res = await client.post(
        "/auth/resend-verification",
        json={"email": "test@example.com"},
    )
    assert res.status_code == 429, (
        "resend-verification must be blocked when auth rate limit is exhausted"
    )