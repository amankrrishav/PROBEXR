"""
LLM provider: OpenAI-compatible chat completions (Groq, OpenAI, OpenRouter).
Uses httpx for async, serverless-friendly.
"""
import httpx
from app.config import get_config


async def chat_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.4,
) -> str:
    """
    Call OpenAI-compatible chat completions API.
    Raises httpx.HTTPStatusError or ValueError on config/response errors.
    """
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
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=cfg.summarize_timeout_seconds) as client:
        response = await client.post(url, json=payload, headers=headers)

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

    data = response.json()
    choice = (data.get("choices") or [None])[0]
    if not choice:
        raise ValueError("No completion in response")
    content = (choice.get("message") or {}).get("content") or ""
    return content.strip()
