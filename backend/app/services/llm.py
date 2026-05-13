"""
LLM provider: OpenAI-compatible chat completions (Groq, OpenAI, OpenRouter).
Uses httpx for async, serverless-friendly.

Provides two interfaces:
  - generate_full()   — returns complete response text (default)
  - generate_stream() — returns async iterator of content deltas (Phase 2B transport)
  - chat_completion() — backward-compatible alias for generate_full()
"""

import logging
import time
from collections.abc import AsyncIterator

import httpx

from app.config import get_config
from app.http_client import get_http_client

logger = logging.getLogger(__name__)

# Estimated cost per 1K tokens (USD) — conservative defaults.
# Update when switching models or providers.
_COST_PER_1K: dict[str, tuple[float, float]] = {
    # (prompt_per_1k, completion_per_1k)
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4-turbo": (0.01, 0.03),
    "gpt-3.5-turbo": (0.0005, 0.0015),
    "llama-3.1-70b-versatile": (0.00059, 0.00079),
    "llama-3.1-8b-instant": (0.00005, 0.00008),
    "mixtral-8x7b-32768": (0.00024, 0.00024),
    "gemma2-9b-it": (0.0002, 0.0002),
}


def _record_usage(response_data: dict, model: str) -> None:
    """Extract token usage from LLM response and record to Prometheus."""
    from app.metrics import LLM_COST_USD, LLM_TOKENS_TOTAL

    usage = response_data.get("usage")
    if not usage:
        return

    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)

    LLM_TOKENS_TOTAL.labels(model=model, type="prompt").inc(prompt_tokens)
    LLM_TOKENS_TOTAL.labels(model=model, type="completion").inc(completion_tokens)

    # Estimate cost
    model_lower = model.lower()
    costs = _COST_PER_1K.get(model_lower)
    if not costs:
        # Try partial match (e.g. "llama-3.1-70b-versatile" in "groq/llama-3.1-70b-versatile")
        for key, val in _COST_PER_1K.items():
            if key in model_lower:
                costs = val
                break

    if costs:
        prompt_cost = (prompt_tokens / 1000) * costs[0]
        completion_cost = (completion_tokens / 1000) * costs[1]
        total_cost = prompt_cost + completion_cost
        LLM_COST_USD.labels(model=model).inc(total_cost)
        logger.info(
            "LLM usage: prompt=%d completion=%d est_cost=$%.6f",
            prompt_tokens,
            completion_tokens,
            total_cost,
        )
    else:
        logger.info(
            "LLM usage: prompt=%d completion=%d (no cost estimate for model=%s)",
            prompt_tokens,
            completion_tokens,
            model,
        )


def _build_request(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.4,
    stream: bool = False,
) -> tuple[str, dict[str, str], dict[str, object]]:
    """Build the URL, headers, and payload for an LLM API call. Shared by full/stream."""
    cfg = get_config()
    base_url = cfg.get_llm_base_url()
    api_key = cfg.get_llm_api_key()
    resolved_model = model or cfg.summarize_model
    if not resolved_model:
        raise ValueError("No model configured. Set SUMMARIZE_MODEL or provider-specific model env.")

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": resolved_model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream,
    }
    return url, headers, payload


def _handle_error_status(response: httpx.Response) -> None:
    """Raise descriptive errors for common upstream failures."""
    if response.status_code == 504:
        raise httpx.HTTPStatusError(
            "Summarization timed out. Try a shorter text.",
            request=response.request,
            response=response,
        )
    if response.status_code == 401:
        raise httpx.HTTPStatusError(
            "Invalid API key. Check your provider key.",
            request=response.request,
            response=response,
        )
    if response.status_code == 429:
        raise httpx.HTTPStatusError(
            "Rate limit exceeded. Try again in a moment.",
            request=response.request,
            response=response,
        )
    response.raise_for_status()


async def generate_full(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.4,
) -> str:
    """
    Call OpenAI-compatible chat completions API and return the full response text.
    Retries up to 2 times on transient errors (429, 502, 503, 504) with exponential backoff.
    Raises httpx.HTTPStatusError or ValueError on config/response errors.
    """
    import asyncio

    from app.metrics import LLM_CALLS_TOTAL, LLM_LATENCY_SECONDS

    url, headers, payload = _build_request(
        messages, model=model, max_tokens=max_tokens, temperature=temperature, stream=False
    )

    cfg = get_config()
    timeout = httpx.Timeout(cfg.summarize_timeout_seconds, connect=10.0)

    _RETRYABLE_STATUSES = {429, 502, 503, 504}
    _MAX_RETRIES = 2
    last_error: Exception | None = None
    resolved_model = payload["model"]

    for attempt in range(_MAX_RETRIES + 1):
        t0 = time.monotonic()
        status_code = 0
        try:
            client = get_http_client()
            response = await client.post(url, json=payload, headers=headers, timeout=timeout)

            elapsed = time.monotonic() - t0
            status_code = response.status_code

            # Instrument latency
            LLM_LATENCY_SECONDS.labels(model=resolved_model, method="generate_full").observe(elapsed)

            logger.info(
                "LLM call completed",
                extra={
                    "elapsed_s": round(elapsed, 2),
                    "model": resolved_model,
                    "status": status_code,
                    "attempt": attempt + 1,
                },
            )

            if response.status_code in _RETRYABLE_STATUSES and attempt < _MAX_RETRIES:
                LLM_CALLS_TOTAL.labels(
                    model=resolved_model,
                    method="generate_full",
                    status=status_code,
                    result="retry",
                ).inc()
                wait = (2**attempt) + 0.5  # 1.5s, 2.5s
                logger.warning(
                    "Retryable LLM error %d, waiting %.1fs (attempt %d/%d)",
                    response.status_code,
                    wait,
                    attempt + 1,
                    _MAX_RETRIES + 1,
                )
                await asyncio.sleep(wait)
                continue

            _handle_error_status(response)

            LLM_CALLS_TOTAL.labels(
                model=resolved_model,
                method="generate_full",
                status=status_code,
                result="success",
            ).inc()

            data = response.json()
            choice = (data.get("choices") or [None])[0]
            if not choice:
                raise ValueError("No completion in response")
            content = (choice.get("message") or {}).get("content") or ""

            # Track token usage and estimated cost
            _record_usage(data, str(resolved_model))

            return content.strip()

        except Exception as e:
            elapsed = time.monotonic() - t0
            last_error = e

            # Record failed attempts in metrics
            LLM_CALLS_TOTAL.labels(
                model=resolved_model,
                method="generate_full",
                status=getattr(getattr(e, "response", None), "status_code", 0),
                result="failure",
            ).inc()

            if isinstance(e, httpx.RequestError) and attempt < _MAX_RETRIES:
                wait = (2**attempt) + 0.5
                logger.warning(
                    "LLM request error: %s, retrying in %.1fs (attempt %d/%d)",
                    str(e),
                    wait,
                    attempt + 1,
                    _MAX_RETRIES + 1,
                )
                await asyncio.sleep(wait)
            else:
                raise

    # Should not reach here, but just in case
    raise last_error or ValueError("LLM request failed after retries")


async def generate_stream(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.4,
) -> AsyncIterator[str]:
    """
    Call OpenAI-compatible chat completions API with streaming enabled.
    Yields content deltas as they arrive.
    """
    import json as _json

    from app.metrics import LLM_CALLS_TOTAL, LLM_LATENCY_SECONDS

    url, headers, payload = _build_request(
        messages, model=model, max_tokens=max_tokens, temperature=temperature, stream=True
    )

    cfg = get_config()
    timeout = httpx.Timeout(cfg.summarize_timeout_seconds, connect=10.0)
    resolved_model = payload["model"]

    t0 = time.monotonic()
    try:
        client = get_http_client()
        async with client.stream("POST", url, json=payload, headers=headers, timeout=timeout) as response:
            _handle_error_status(response)
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = _json.loads(data_str)
                    delta = (chunk.get("choices") or [{}])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content
                except _json.JSONDecodeError:
                    continue

            elapsed = time.monotonic() - t0
            LLM_LATENCY_SECONDS.labels(model=resolved_model, method="generate_stream").observe(elapsed)
            LLM_CALLS_TOTAL.labels(model=resolved_model, method="generate_stream", status=200, result="success").inc()
            logger.info("LLM stream completed", extra={"elapsed_s": round(elapsed, 2), "model": resolved_model})

    except Exception as e:
        LLM_CALLS_TOTAL.labels(
            model=resolved_model,
            method="generate_stream",
            status=getattr(getattr(e, "response", None), "status_code", 0),
            result="failure",
        ).inc()
        raise


# Backward-compatible alias — all existing callers use this
chat_completion = generate_full
