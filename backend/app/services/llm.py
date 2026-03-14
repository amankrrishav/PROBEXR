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
from typing import AsyncIterator

import httpx
from app.config import get_config

logger = logging.getLogger(__name__)


def _build_request(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.4,
    stream: bool = False,
) -> tuple[str, dict[str, str], dict]:
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
    from app.metrics import LLM_LATENCY_SECONDS, LLM_CALLS_TOTAL

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
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
            
            elapsed = time.monotonic() - t0
            status_code = response.status_code
            
            # Instrument latency
            LLM_LATENCY_SECONDS.labels(model=resolved_model, method="generate_full").observe(elapsed)

            logger.info(
                "LLM call completed",
                extra={"elapsed_s": round(elapsed, 2), "model": resolved_model,
                       "status": status_code, "attempt": attempt + 1},
            )

            if response.status_code in _RETRYABLE_STATUSES and attempt < _MAX_RETRIES:
                LLM_CALLS_TOTAL.labels(model=resolved_model, method="generate_full", status=status_code, result="retry").inc()
                wait = (2 ** attempt) + 0.5  # 1.5s, 2.5s
                logger.warning(
                    "Retryable LLM error %d, waiting %.1fs (attempt %d/%d)",
                    response.status_code, wait, attempt + 1, _MAX_RETRIES + 1,
                )
                await asyncio.sleep(wait)
                continue

            _handle_error_status(response)

            LLM_CALLS_TOTAL.labels(model=resolved_model, method="generate_full", status=status_code, result="success").inc()
            
            data = response.json()
            choice = (data.get("choices") or [None])[0]
            if not choice:
                raise ValueError("No completion in response")
            content = (choice.get("message") or {}).get("content") or ""
            return content.strip()

        except Exception as e:
            elapsed = time.monotonic() - t0
            last_error = e
            
            # Record failed attempts in metrics
            LLM_CALLS_TOTAL.labels(
                model=resolved_model, 
                method="generate_full", 
                status=getattr(e, "response", None).status_code if hasattr(e, "response") else 0,
                result="failure"
            ).inc()

            if isinstance(e, httpx.RequestError) and attempt < _MAX_RETRIES:
                wait = (2 ** attempt) + 0.5
                logger.warning(
                    "LLM request error: %s, retrying in %.1fs (attempt %d/%d)",
                    str(e), wait, attempt + 1, _MAX_RETRIES + 1,
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
    from app.metrics import LLM_LATENCY_SECONDS, LLM_CALLS_TOTAL

    url, headers, payload = _build_request(
        messages, model=model, max_tokens=max_tokens, temperature=temperature, stream=True
    )

    cfg = get_config()
    timeout = httpx.Timeout(cfg.summarize_timeout_seconds, connect=10.0)
    resolved_model = payload["model"]

    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
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
            status=getattr(e, "response", None).status_code if hasattr(e, "response") else 0,
            result="failure"
        ).inc()
        raise


# Backward-compatible alias — all existing callers use this
chat_completion = generate_full
