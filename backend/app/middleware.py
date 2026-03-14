import logging
import secrets
import time
from typing import Callable, Awaitable, Protocol, Optional

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
        api_logger = logging.getLogger("api")
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            api_logger.exception("Request failed with exception")
            raise
        finally:
            process_time = time.time() - start_time
            api_logger.info(
                "Request handled",
                extra={
                    "method": request.method,
                    "url": str(request.url.path),
                    "status_code": status_code,
                    "process_time_s": process_time,
                }
            )
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


class RateLimitingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        cfg = get_config()
        client_ip = request.client.host if request.client else "unknown"
        path = str(request.url.path)

        current_minute = int(time.time() // 60)

        # Routes that hit LLM / scraping — given a tighter budget
        is_llm_route = any(p in path for p in ["/summarize", "/api/synthesis", "/api/chat", "/api/tts", "/api/ingest"])
        tier = "llm" if is_llm_route else "general"
        limit = cfg.rate_limit_llm_per_minute if is_llm_route else cfg.rate_limit_per_minute

        key = f"rl:{client_ip}:{tier}:{current_minute}"

        limiter = get_rate_limiter()
        allowed, current_count = await limiter.check_and_increment(key, limit)

        # Standard rate-limit headers (RFC 6585 / draft-ietf-httpapi-ratelimit-headers)
        remaining = max(0, limit - current_count)
        reset_at = (current_minute + 1) * 60  # start of next window
        rl_headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_at),
        }

        if not allowed:
            logger.info("Rate limit hit", extra={"client_ip": client_ip, "tier": tier, "limit": limit})
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={**rl_headers, "Retry-After": str(reset_at - int(time.time()))},
            )

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

# Paths that are exempt from CSRF checks (public APIs and OAuth redirects)
_CSRF_EXEMPT_PREFIXES: tuple[str, ...] = (
    "/api/v1/health",
    "/api/v1/metrics",
    "/api/v1/auth/google/callback",
    "/api/v1/auth/github/callback",
    "/api/v1/auth/verify",          # magic link verification (GET with token param)
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
    Dual-submit cookie CSRF protection.

    - Sets a `csrf_token` cookie (readable by JS) on every response.
    - Validates that `X-CSRF-Token` header matches the cookie on mutating requests.
    - Exempt paths and safe HTTP methods are allowed through unconditionally.
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

        # --- Validate CSRF on mutating requests ---
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)

        if not cookie_token or not header_token:
            logger.warning(
                "CSRF token missing",
                extra={"path": path, "method": request.method, "has_cookie": bool(cookie_token), "has_header": bool(header_token)},
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing. Please refresh the page and try again."},
            )

        if not secrets.compare_digest(cookie_token, header_token):
            logger.warning(
                "CSRF token mismatch",
                extra={"path": path, "method": request.method},
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token mismatch. Please refresh the page and try again."},
            )

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
