import logging
import time
from typing import Callable, Awaitable, Protocol

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
    def check_and_increment(self, key: str, limit: int) -> bool:
        """Return True if the request should be allowed, False if rate-limited."""
        ...

    def cleanup(self, current_minute: int) -> None:
        """Evict stale entries."""
        ...


class InMemoryRateLimiter:
    """In-memory rate limiter. Suitable for single-process deployments."""
    def __init__(self) -> None:
        self._data: dict[str, int] = {}

    def check_and_increment(self, key: str, limit: int) -> bool:
        current_hits = self._data.get(key, 0)
        if current_hits >= limit:
            return False
        self._data[key] = current_hits + 1
        return True

    def cleanup(self, current_minute: int) -> None:
        """Evict keys from previous minutes to prevent unbounded growth."""
        stale_keys = [
            k for k in self._data
            if not k.endswith(f"_{current_minute}")
        ]
        for sk in stale_keys:
            self._data.pop(sk, None)


# Singleton — swap with RedisRateLimiter when Redis is available
_rate_limiter = InMemoryRateLimiter()


class RateLimitingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        cfg = get_config()
        client_ip = request.client.host if request.client else "unknown"
        path = str(request.url.path)

        current_minute = int(time.time() // 60)

        # Routes that hit LLM / scraping — given a tighter budget
        is_llm_route = any(p in path for p in ["/summarize", "/api/synthesis", "/api/chat", "/api/tts", "/api/ingest"])
        limit = cfg.rate_limit_llm_per_minute if is_llm_route else cfg.rate_limit_per_minute

        key = f"{client_ip}_{is_llm_route}_{current_minute}"

        # Proactive cleanup every cycle
        _rate_limiter.cleanup(current_minute)

        if not _rate_limiter.check_and_increment(key, limit):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."}
            )

        return await call_next(request)
