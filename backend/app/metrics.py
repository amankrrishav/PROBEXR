from prometheus_client import Histogram, Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# LLM Latency Histogram
LLM_LATENCY_SECONDS = Histogram(
    "llm_latency_seconds",
    "Time spent in LLM API calls",
    ["model", "method"],
    buckets=(1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, float("inf")),
)

# LLM Calls Counter
LLM_CALLS_TOTAL = Counter(
    "llm_calls_total",
    "Total number of LLM API calls",
    ["model", "method", "status", "result"],
)

def metrics_endpoint():
    """Returns the latest Prometheus metrics in text format."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
