import logging
import time
from pythonjsonlogger import jsonlogger
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

def setup_logging() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(  # type: ignore
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    
    # Disable uvicorn access logs to avoid double logging
    logging.getLogger("uvicorn.access").disabled = True

from typing import Callable, Awaitable
from fastapi import Response

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        logger = logging.getLogger("api")
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            logger.error("Request failed with exception", extra={"error": str(e)})
            raise
        finally:
            process_time = time.time() - start_time
            logger.info(
                "Request handled",
                extra={
                    "method": request.method,
                    "url": str(request.url.path),
                    "status_code": status_code,
                    "process_time_s": process_time,
                }
            )
        return response

from app.config import get_config
from fastapi.responses import JSONResponse

_rate_limit_data: dict[str, int] = {}

class RateLimitingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        cfg = get_config()
        client_ip = request.client.host if request.client else "unknown"
        path = str(request.url.path)
        
        # Simple minute-bucketing
        current_minute = int(time.time() // 60)
        
        # Distinguish LLM routes
        is_llm_route = any(p in path for p in ["/summarize", "/api/synthesis", "/api/chat", "/api/tts"])
        limit = cfg.rate_limit_llm_per_minute if is_llm_route else cfg.rate_limit_per_minute
        
        # Clean up old minute data intermittently
        if len(_rate_limit_data) > 10000:
            _rate_limit_data.clear()
            
        key = f"{client_ip}_{is_llm_route}_{current_minute}"
        
        current_hits = _rate_limit_data.get(key, 0)
        if current_hits >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."}
            )
            
        _rate_limit_data[key] = current_hits + 1
        return await call_next(request)
