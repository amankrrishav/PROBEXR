"""
tests/test_prometheus_metrics.py — A-35: Prometheus metrics for routes and auth

Verifies HTTP route metrics and auth event counters are defined,
that the /metrics endpoint is reachable, and that auth events
are instrumented at key points in the auth router.
"""
import inspect
import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Metrics definitions
# ---------------------------------------------------------------------------

def test_http_request_duration_histogram_defined():
    """HTTP_REQUEST_DURATION_SECONDS histogram must be defined in metrics.py."""
    from app.metrics import HTTP_REQUEST_DURATION_SECONDS
    assert HTTP_REQUEST_DURATION_SECONDS is not None


def test_http_requests_total_counter_defined():
    """HTTP_REQUESTS_TOTAL counter must be defined in metrics.py."""
    from app.metrics import HTTP_REQUESTS_TOTAL
    assert HTTP_REQUESTS_TOTAL is not None


def test_auth_events_total_counter_defined():
    """AUTH_EVENTS_TOTAL counter must be defined in metrics.py."""
    from app.metrics import AUTH_EVENTS_TOTAL
    assert AUTH_EVENTS_TOTAL is not None


def test_http_duration_has_method_path_status_labels():
    """HTTP_REQUEST_DURATION_SECONDS must have method, path, status_code labels."""
    from app.metrics import HTTP_REQUEST_DURATION_SECONDS
    label_names = HTTP_REQUEST_DURATION_SECONDS._labelnames
    assert "method" in label_names
    assert "path" in label_names
    assert "status_code" in label_names


def test_auth_events_has_event_label():
    """AUTH_EVENTS_TOTAL must have an event label."""
    from app.metrics import AUTH_EVENTS_TOTAL
    assert "event" in AUTH_EVENTS_TOTAL._labelnames


# ---------------------------------------------------------------------------
# /metrics endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_metrics_endpoint_reachable(client: AsyncClient):
    """GET /metrics must return 200 with Prometheus text format."""
    res = await client.get("/metrics")
    assert res.status_code == 200
    assert "text/plain" in res.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_metrics_endpoint_contains_llm_metrics(client: AsyncClient):
    """Metrics output must include existing LLM metrics."""
    res = await client.get("/metrics")
    assert res.status_code == 200
    assert "llm_latency_seconds" in res.text or "llm_calls_total" in res.text


@pytest.mark.asyncio
async def test_metrics_endpoint_contains_http_metrics(client: AsyncClient):
    """Metrics output must include HTTP route metrics after at least one request."""
    # Make a request first so the counter is non-zero
    await client.get("/")
    res = await client.get("/metrics")
    assert res.status_code == 200
    assert "http_requests_total" in res.text or "http_request_duration_seconds" in res.text


# ---------------------------------------------------------------------------
# Auth event instrumentation
# ---------------------------------------------------------------------------

def test_auth_router_instruments_login_failure():
    """auth router must increment AUTH_EVENTS_TOTAL on login failure."""
    import app.routers.auth as auth_router
    src = inspect.getsource(auth_router.login)
    assert 'AUTH_EVENTS_TOTAL.labels(event="login_failure")' in src, (
        "login endpoint must record login_failure metric"
    )


def test_auth_router_instruments_login_success():
    """auth router must increment AUTH_EVENTS_TOTAL on login success."""
    import app.routers.auth as auth_router
    src = inspect.getsource(auth_router.login)
    assert 'AUTH_EVENTS_TOTAL.labels(event="login_success")' in src, (
        "login endpoint must record login_success metric"
    )


def test_auth_router_instruments_logout():
    """auth router must increment AUTH_EVENTS_TOTAL on logout."""
    import app.routers.auth as auth_router
    src = inspect.getsource(auth_router.logout)
    assert 'AUTH_EVENTS_TOTAL.labels(event="logout")' in src, (
        "logout endpoint must record logout metric"
    )


def test_auth_router_instruments_token_refresh():
    """auth router must increment AUTH_EVENTS_TOTAL on token refresh."""
    import app.routers.auth as auth_router
    src = inspect.getsource(auth_router.refresh)
    assert 'AUTH_EVENTS_TOTAL.labels(event="token_refresh")' in src, (
        "refresh endpoint must record token_refresh metric"
    )


def test_logging_middleware_records_http_metrics():
    """LoggingMiddleware must call HTTP_REQUEST_DURATION_SECONDS and HTTP_REQUESTS_TOTAL."""
    from app.middleware import LoggingMiddleware
    src = inspect.getsource(LoggingMiddleware.dispatch)
    assert "HTTP_REQUEST_DURATION_SECONDS" in src, (
        "LoggingMiddleware must record request duration metric"
    )
    assert "HTTP_REQUESTS_TOTAL" in src, (
        "LoggingMiddleware must record request count metric"
    )