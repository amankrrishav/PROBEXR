import hashlib
import json
import logging
import secrets
import time
from typing import Callable, Awaitable, Protocol, Optional

import jwt

from pythonjsonlogger import jsonlogger
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_config

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    logHandler.setFormatter(formatter)
    root_logger.addHandler(logHandler)
    
    # Disable uvicorn access logs to avoid double logging
    logging.getLogger("uvicorn.access").disabled = True


from fastapi import Response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        from app.metrics import HTTP_REQUEST_DURATION_SECONDS, HTTP_REQUESTS_TOTAL

        api_logger = logging.getLogger("api")
        start_time = time.time()

        # A-34: Generate or propagate a request ID for log correlation.
        # Clients can send X-Request-ID; if absent we generate one.
        request_id = request.headers.get("x-request-id") or secrets.token_hex(8)

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            api_logger.exception(
                "Request failed with exception",
                extra={"request_id": request_id},
            )
            raise
        finally:
            process_time = time.time() - start_time
            path = str(request.url.path)

            api_logger.info(
                "Request handled",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": path,
                    "status_code": status_code,
                    "process_time_s": round(process_time, 4),
                },
            )

            # A-35: Record HTTP route metrics
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                path=path,
                status_code=str(status_code),
            ).observe(process_time)
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                path=path,
                status_code=str(status_code),
            ).inc()

        # A-34: Propagate request ID back to caller in response header
        response.headers["X-Request-ID"] = request_id
        return response


# --- Rate Limiter Abstraction ---

class RateLimiterBackend(Protocol):
    """Protocol for rate limiter backends. Implementations can use Redis, in-memory, etc."""
    async def check_and_increment(self, key: str, limit: int) -> tuple[bool, int]:
        """Return (allowed, current_count). allowed=True if under limit."""
        ...


class InMemoryRateLimiter:
    """In-memory rate limiter. Suitable for single-process deployments and dev fallback."""
    def __init__(self) -> None:
        self._data: dict[str, int] = {}
        self._current_minute: int = 0

    async def check_and_increment(self, key: str, limit: int) -> tuple[bool, int]:
        current_minute = int(time.time() // 60)
        # Cleanup stale keys when minute changes
        if current_minute != self._current_minute:
            self._data.clear()
            self._current_minute = current_minute

        current_hits = self._data.get(key, 0)
        if current_hits >= limit:
            return False, current_hits
        self._data[key] = current_hits + 1
        return True, current_hits + 1


class RedisRateLimiter:
    """Redis-backed rate limiter using atomic INCR + EXPIRE."""
    def __init__(self, redis_client: "redis.asyncio.Redis") -> None:  # type: ignore
        self._redis = redis_client

    async def check_and_increment(self, key: str, limit: int) -> tuple[bool, int]:
        try:
            current = await self._redis.incr(key)
            if current == 1:
                # First request in this window — set TTL to 60s
                await self._redis.expire(key, 60)
            return current <= limit, int(current)
        except Exception:
            # Redis error → allow the request (fail-open)
            logger.warning("Redis rate limiter error, allowing request", exc_info=True)
            return True, 0


# Global rate limiter — set during startup
_rate_limiter: Optional[RateLimiterBackend] = None  # type: ignore


def get_rate_limiter() -> RateLimiterBackend:  # type: ignore
    """Return the active rate limiter (Redis or in-memory fallback)."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = InMemoryRateLimiter()
    return _rate_limiter


def set_rate_limiter(limiter: RateLimiterBackend) -> None:  # type: ignore
    """Set the active rate limiter (called during app startup)."""
    global _rate_limiter
    _rate_limiter = limiter


_AUTH_RATE_LIMITED_PATHS = (
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/magic-link",
    "/api/v1/auth/forgot-password",    # triggers SMTP send — prevent email spam
    "/api/v1/auth/resend-verification", # triggers SMTP send — prevent email spam
)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        cfg = get_config()
        client_ip = request.client.host if request.client else "unknown"
        path = str(request.url.path)

        current_minute = int(time.time() // 60)

        # Determine tier and limit
        is_auth_route = any(path.startswith(p) for p in _AUTH_RATE_LIMITED_PATHS)
        is_llm_route = not is_auth_route and any(
            p in path for p in ["/summarize", "/api/synthesis", "/api/chat", "/api/tts", "/api/ingest"]
        )

        if is_auth_route:
            tier = "auth"
            limit = cfg.rate_limit_auth_per_minute
        elif is_llm_route:
            tier = "llm"
            limit = cfg.rate_limit_llm_per_minute
        else:
            tier = "general"
            limit = cfg.rate_limit_per_minute

        limiter = get_rate_limiter()
        reset_at = (current_minute + 1) * 60

        # --- IP-based check (always) ---
        ip_key = f"rl:{client_ip}:{tier}:{current_minute}"
        ip_allowed, ip_count = await limiter.check_and_increment(ip_key, limit)

        if not ip_allowed:
            logger.info(
                "Rate limit hit (IP)",
                extra={"client_ip": client_ip, "tier": tier, "limit": limit},
            )
            rl_headers = {
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_at),
                "Retry-After": str(reset_at - int(time.time())),
            }
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down and try again later."},
                headers=rl_headers,
            )

        # --- Per-user check (authenticated non-auth routes) ---
        # Decodes the access_token cookie JWT to get the user's identity without
        # a DB round-trip. Hashes the sub claim so no PII is stored in the
        # rate-limit store. Prevents a heavy user on a shared IP (corporate VPN,
        # university) from consuming the entire IP quota for everyone else.
        if not is_auth_route:
            raw_token = request.cookies.get("access_token", "")
            if raw_token.startswith("Bearer "):
                raw_token = raw_token[len("Bearer "):]
            if raw_token:
                try:
                    payload = jwt.decode(
                        raw_token,
                        cfg.verification_key,
                        algorithms=[cfg.algorithm],
                        options={"verify_exp": False},  # expiry enforced by auth layer
                    )
                    sub = payload.get("sub", "")
                    if sub:
                        user_hash = hashlib.sha256(sub.strip().lower().encode()).hexdigest()[:32]
                        user_key = f"rl:user:{user_hash}:{tier}:{current_minute}"
                        user_allowed, _ = await limiter.check_and_increment(user_key, limit)
                        if not user_allowed:
                            logger.info(
                                "Rate limit hit (user)",
                                extra={"tier": tier, "limit": limit},
                            )
                            rl_headers = {
                                "X-RateLimit-Limit": str(limit),
                                "X-RateLimit-Remaining": "0",
                                "X-RateLimit-Reset": str(reset_at),
                                "Retry-After": str(reset_at - int(time.time())),
                            }
                            return JSONResponse(
                                status_code=429,
                                content={"detail": "Too many requests. Please slow down and try again later."},
                                headers=rl_headers,
                            )
                except Exception:
                    # Malformed / expired token — fall through, IP check already passed
                    pass

        # --- Per-email check (auth routes only, POST with JSON body) ---
        if is_auth_route and request.method == "POST":
            try:
                body_bytes = await request.body()
                # Re-inject body so downstream handlers can still read it
                request._body = body_bytes  # type: ignore[attr-defined]
                body_data = json.loads(body_bytes)
                email = body_data.get("email", "")
                if email and isinstance(email, str):
                    email_hash = hashlib.sha256(email.strip().lower().encode()).hexdigest()[:32]
                    email_key = f"rl:email:{email_hash}:{tier}:{current_minute}"
                    email_allowed, _ = await limiter.check_and_increment(email_key, limit)
                    if not email_allowed:
                        logger.info(
                            "Rate limit hit (email)",
                            extra={"tier": tier, "limit": limit},
                        )
                        rl_headers = {
                            "X-RateLimit-Limit": str(limit),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(reset_at),
                            "Retry-After": str(reset_at - int(time.time())),
                        }
                        return JSONResponse(
                            status_code=429,
                            content={"detail": "Too many requests for this account. Try again later."},
                            headers=rl_headers,
                        )
            except Exception:
                # Body parsing failed — fall through, IP check already passed
                pass

        # --- Standard rate-limit headers on success ---
        remaining = max(0, limit - ip_count)
        rl_headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_at),
        }

        response = await call_next(request)
        for header, value in rl_headers.items():
            response.headers[header] = value
        return response


# ---------------------------------------------------------------------------
# CSRF Protection — Dual-Submit Cookie Pattern
# ---------------------------------------------------------------------------
# How it works:
#   1. Every response sets a `csrf_token` cookie (NOT HttpOnly → JS can read it).
#   2. The frontend reads this cookie and sends it back as the `X-CSRF-Token` header.
#   3. On state-changing requests (POST/PUT/PATCH/DELETE), the middleware checks
#      that the header value matches the cookie value.
#   4. An attacker's cross-site form cannot read our cookie, so they cannot set the
#      header — the request is rejected.
#
# Safe methods (GET/HEAD/OPTIONS) are always allowed through.
# Certain paths (health, metrics, OAuth callbacks) are exempt.
# ---------------------------------------------------------------------------

# Paths that are exempt from CSRF checks (public APIs, OAuth redirects, pre-auth endpoints)
# Login/register are intentionally NOT exempt — they're protected by either:
#   - Origin-header check (cross-domain deployments)
#   - Dual-submit cookie (same-domain fallback)
_CSRF_EXEMPT_PREFIXES: tuple[str, ...] = (
    "/api/v1/health",
    "/api/v1/metrics",
    "/api/v1/auth/google/callback",     # OAuth callback (state cookie validates CSRF)
    "/api/v1/auth/github/callback",     # OAuth callback (state cookie validates CSRF)
    "/api/v1/auth/verify-email",        # GET-only, but exempt for safety
    "/docs",
    "/openapi.json",
    "/redoc",
)

# Methods that never mutate state — always safe
_CSRF_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection that works for both same-domain and cross-domain deployments.

    Two complementary strategies:
      1. **Origin-header check** (cross-domain):
         If the request has an `Origin` header and it matches one of the allowed
         CORS origins, the request is trusted.  Browsers always attach `Origin`
         on cross-origin requests, and it CANNOT be forged by JavaScript — an
         attacker site would send its own origin, which won't be in our allow list.

      2. **Dual-submit cookie** (same-domain fallback):
         If no `Origin` header is present (e.g. same-origin requests on some
         older browsers), fall back to the classic cookie-vs-header check.

    Exempt paths and safe HTTP methods are always allowed through.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        cfg = get_config()
        path = request.url.path

        # --- Skip CSRF for safe methods ---
        if request.method in _CSRF_SAFE_METHODS:
            response = await call_next(request)
            self._ensure_csrf_cookie(response, request, cfg)
            return response

        # --- Skip CSRF for exempt paths ---
        if any(path.startswith(prefix) for prefix in _CSRF_EXEMPT_PREFIXES):
            response = await call_next(request)
            self._ensure_csrf_cookie(response, request, cfg)
            return response

        # --- Strategy 1: Origin-header check (cross-domain) ---
        origin = request.headers.get("origin")
        if origin:
            allowed_origins = [
                o.strip().rstrip("/")
                for o in cfg.cors_origins.split(",")
                if o.strip()
            ]
            if origin.rstrip("/") in allowed_origins or "*" in allowed_origins:
                # Origin matches our CORS allow list → trusted
                response = await call_next(request)
                self._ensure_csrf_cookie(response, request, cfg)
                return response

            # Origin present but NOT in allow list → reject
            logger.warning(
                "CSRF rejected: origin not allowed",
                extra={"path": path, "origin": origin},
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Origin not allowed."},
            )

        # --- Strategy 2: Dual-submit cookie (same-domain fallback) ---
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)

        if not cookie_token or not header_token:
            logger.warning(
                "CSRF token missing",
                extra={"path": path, "method": request.method, "has_cookie": bool(cookie_token), "has_header": bool(header_token)},
            )
            response = JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing. Please refresh the page and try again."},
            )
            self._ensure_csrf_cookie(response, request, cfg)
            return response

        if not secrets.compare_digest(cookie_token, header_token):
            logger.warning(
                "CSRF token mismatch",
                extra={"path": path, "method": request.method},
            )
            response = JSONResponse(
                status_code=403,
                content={"detail": "CSRF token mismatch. Please refresh the page and try again."},
            )
            self._ensure_csrf_cookie(response, request, cfg)
            return response

        # Token is valid — proceed
        response = await call_next(request)
        self._ensure_csrf_cookie(response, request, cfg)
        return response

    @staticmethod
    def _ensure_csrf_cookie(response: Response, request: Request, cfg: "AppConfig") -> None:  # type: ignore[name-defined]
        """Set or refresh the CSRF cookie on every response."""
        existing = request.cookies.get(CSRF_COOKIE_NAME)
        token = existing or secrets.token_urlsafe(32)
        is_prod = cfg.environment == "production"
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=token,
            httponly=False,        # Frontend JS must be able to read this
            samesite="none" if is_prod else "lax",
            secure=is_prod,
            max_age=60 * 60 * 24,  # 24 hours
            path="/",
        )