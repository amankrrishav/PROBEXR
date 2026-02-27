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
