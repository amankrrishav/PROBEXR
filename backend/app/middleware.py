import logging
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
    async def check_and_increment(self, key: str, limit: int) -> bool:
        """Return True if the request should be allowed, False if rate-limited."""
        ...


class InMemoryRateLimiter:
    """In-memory rate limiter. Suitable for single-process deployments and dev fallback."""
    def __init__(self) -> None:
        self._data: dict[str, int] = {}
        self._current_minute: int = 0

    async def check_and_increment(self, key: str, limit: int) -> bool:
        current_minute = int(time.time() // 60)
        # Cleanup stale keys when minute changes
        if current_minute != self._current_minute:
            self._data.clear()
            self._current_minute = current_minute

        current_hits = self._data.get(key, 0)
        if current_hits >= limit:
            return False
        self._data[key] = current_hits + 1
        return True


class RedisRateLimiter:
    """Redis-backed rate limiter using atomic INCR + EXPIRE."""
    def __init__(self, redis_client: "redis.asyncio.Redis") -> None:  # type: ignore
        self._redis = redis_client

    async def check_and_increment(self, key: str, limit: int) -> bool:
        try:
            current = await self._redis.incr(key)
            if current == 1:
                # First request in this window — set TTL to 60s
                await self._redis.expire(key, 60)
            return current <= limit
        except Exception:
            # Redis error → allow the request (fail-open)
            logger.warning("Redis rate limiter error, allowing request", exc_info=True)
            return True


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
        allowed = await limiter.check_and_increment(key, limit)

        if not allowed:
            logger.info("Rate limit hit", extra={"client_ip": client_ip, "tier": tier, "limit": limit})
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."}
            )

        return await call_next(request)
