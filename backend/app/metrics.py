from prometheus_client import Histogram, Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# ── LLM metrics (existing) ────────────────────────────────────────────────

LLM_LATENCY_SECONDS = Histogram(
    "llm_latency_seconds",
    "Time spent in LLM API calls",
    ["model", "method"],
    buckets=(1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, float("inf")),
)

LLM_CALLS_TOTAL = Counter(
    "llm_calls_total",
    "Total number of LLM API calls",
    ["model", "method", "status", "result"],
)

# ── A-35: HTTP route metrics ──────────────────────────────────────────────

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path", "status_code"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf")),
)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status_code"],
)

# ── A-35: Auth event metrics ──────────────────────────────────────────────

AUTH_EVENTS_TOTAL = Counter(
    "auth_events_total",
    "Total number of authentication events",
    ["event"],  # e.g. login_success, login_failure, register, logout, token_refresh
)


def metrics_endpoint() -> Response:
    """Returns the latest Prometheus metrics in text format."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)