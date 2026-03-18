"""
tests/test_request_id.py — A-34: Request ID in structured logs

Verifies that every response carries an X-Request-ID header,
that client-supplied IDs are echoed back, and that the middleware
source contains the request_id field in log extras.
"""
import inspect
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_response_has_request_id_header(client: AsyncClient):
    """Every response must include an X-Request-ID header."""
    res = await client.get("/")
    assert "x-request-id" in res.headers or "X-Request-ID" in res.headers, (
        "All responses must carry X-Request-ID for log correlation"
    )


@pytest.mark.asyncio
async def test_client_supplied_request_id_is_echoed(client: AsyncClient):
    """If the client sends X-Request-ID, the same value must be echoed back."""
    custom_id = "test-req-abc123"
    res = await client.get("/", headers={"X-Request-ID": custom_id})
    returned_id = res.headers.get("x-request-id") or res.headers.get("X-Request-ID")
    assert returned_id == custom_id, (
        f"Client-supplied X-Request-ID '{custom_id}' must be echoed back, got '{returned_id}'"
    )


@pytest.mark.asyncio
async def test_generated_request_id_is_non_empty(client: AsyncClient):
    """Auto-generated X-Request-ID must be a non-empty string."""
    res = await client.get("/")
    request_id = res.headers.get("x-request-id") or res.headers.get("X-Request-ID", "")
    assert len(request_id) > 0, "Auto-generated X-Request-ID must not be empty"


@pytest.mark.asyncio
async def test_different_requests_get_different_ids(client: AsyncClient):
    """Each request without a supplied ID must get a unique generated ID."""
    res1 = await client.get("/")
    res2 = await client.get("/")
    id1 = res1.headers.get("x-request-id") or res1.headers.get("X-Request-ID")
    id2 = res2.headers.get("x-request-id") or res2.headers.get("X-Request-ID")
    assert id1 != id2, "Each request must get a unique X-Request-ID"


def test_logging_middleware_includes_request_id_in_log_extra():
    """LoggingMiddleware must include request_id in structured log extras."""
    from app.middleware import LoggingMiddleware
    src = inspect.getsource(LoggingMiddleware.dispatch)
    assert "request_id" in src, (
        "LoggingMiddleware must include request_id in log extra fields"
    )


def test_logging_middleware_reads_client_request_id_header():
    """LoggingMiddleware must read X-Request-ID from incoming request headers."""
    from app.middleware import LoggingMiddleware
    src = inspect.getsource(LoggingMiddleware.dispatch)
    assert "x-request-id" in src.lower(), (
        "LoggingMiddleware must read the X-Request-ID header from incoming requests"
    )