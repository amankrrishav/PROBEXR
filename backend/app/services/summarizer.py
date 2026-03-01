"""
Summarization: LLM (human-like) when an API key is set, or free extractive fallback ($0, no key).
"""
import re
from typing import Any
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_config, AppConfig
from app.services.extractive import summarize_extractive
from app.models.user import User

# Lazy import so extractive path works without httpx when no key
_llm = None


def _get_llm() -> Any:
    global _llm
    if _llm is None:
        from app.services import llm as m

        _llm = m
    return _llm


def _clean_text(text: str) -> str:
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _target_words(original_word_count: int, cfg: AppConfig) -> int:
    """
    Compute target word count for LLM summaries.
    """
    base = max(cfg.target_min_words, int(original_word_count * 0.25))
    return min(base, cfg.target_max_words)


async def summarize(text: str) -> str:
    """
    If an API key is set: use LLM (human-like, two-stage).
    Otherwise: use extractive fallback ($0, no API).
    """
    cfg = get_config()
    text = _clean_text(text)
    words = text.split()
    if len(words) < cfg.min_words:
        raise ValueError(f"Text too short. Minimum {cfg.min_words} words.")

    # Extractive path: when no LLM provider exists.
    if not cfg.has_llm_provider:
        return summarize_extractive(
            text,
            min_words=cfg.min_words,
            target_min=cfg.target_min_words,
            target_max=cfg.target_max_words,
        )

    # LLM path: two-stage (extract → synthesize)
    llm = _get_llm()
    original_word_count = len(words)
    target_words = _target_words(original_word_count, cfg)

    extraction_system = """You are an expert reader. Your job is to extract the core ideas from an article—not to rewrite it.
Output clear, concise notes: thesis, main arguments, key evidence or examples, any counterpoints, and implications or takeaways.
Be structured (bullets or short lines). Do not paraphrase into full sentences yet."""

    extraction_user = f"Article:\n\n{text}"

    structured_notes = await llm.chat_completion(
        [
            {"role": "system", "content": extraction_system},
            {"role": "user", "content": extraction_user},
        ],
        max_tokens=1024,
        temperature=0.2,
    )

    if not structured_notes.strip():
        raise ValueError("Could not extract ideas from the text. Try a different article.")

    synthesis_system = """You are a skilled explainer. Using only the notes provided, write a short summary as if you understood the topic and are explaining it to a colleague.
Write in clear, natural prose. Preserve important facts and nuance. Do not copy phrases from the notes verbatim—use your own words. Keep a formal but readable tone."""

    synthesis_user = f"""Notes:
{structured_notes}

Write a cohesive summary of approximately {target_words} words. One or two short paragraphs. No bullet points."""

    final_summary = await llm.chat_completion(
        [
            {"role": "system", "content": synthesis_system},
            {"role": "user", "content": synthesis_user},
        ],
        max_tokens=600,
        temperature=0.4,
    )

    return final_summary.strip() or "Summary could not be generated."


class SummarizePrepResult:
    """Result of prepare_summarize_messages — either an extractive fallback or LLM messages ready to stream."""
    def __init__(
        self,
        *,
        extractive_result: str | None = None,
        messages: list[dict[str, str]] | None = None,
        max_tokens: int = 600,
        temperature: float = 0.4,
    ):
        self.extractive_result = extractive_result
        self.messages = messages
        self.max_tokens = max_tokens
        self.temperature = temperature

    @property
    def is_extractive(self) -> bool:
        return self.extractive_result is not None


async def prepare_summarize_messages(text: str) -> SummarizePrepResult:
    """
    Validate and prepare for summarization.

    Returns a SummarizePrepResult:
      - If no LLM provider: contains extractive_result
      - If LLM available: runs Stage 1 extraction (non-streaming), then returns
        the Stage 2 synthesis messages ready for streaming.

    Raises ValueError on validation failure or extraction failure.
    """
    cfg = get_config()
    text = _clean_text(text)
    words = text.split()

    if len(words) < cfg.min_words:
        raise ValueError(f"Text too short. Minimum {cfg.min_words} words.")

    # Extractive fallback
    if not cfg.has_llm_provider:
        result = summarize_extractive(
            text,
            min_words=cfg.min_words,
            target_min=cfg.target_min_words,
            target_max=cfg.target_max_words,
        )
        return SummarizePrepResult(extractive_result=result)

    # LLM path: Stage 1 — extraction (non-streaming)
    llm = _get_llm()
    original_word_count = len(words)
    target = _target_words(original_word_count, cfg)

    extraction_system = """You are an expert reader. Your job is to extract the core ideas from an article—not to rewrite it.
Output clear, concise notes: thesis, main arguments, key evidence or examples, any counterpoints, and implications or takeaways.
Be structured (bullets or short lines). Do not paraphrase into full sentences yet."""

    structured_notes = await llm.chat_completion(
        [
            {"role": "system", "content": extraction_system},
            {"role": "user", "content": f"Article:\n\n{text}"},
        ],
        max_tokens=1024,
        temperature=0.2,
    )

    if not structured_notes.strip():
        raise ValueError("Could not extract ideas from the text.")

    # Stage 2 messages (ready for streaming or full call)
    synthesis_system = """You are a skilled explainer. Using only the notes provided, write a short summary as if you understood the topic and are explaining it to a colleague.
Write in clear, natural prose. Preserve important facts and nuance. Do not copy phrases from the notes verbatim—use your own words. Keep a formal but readable tone."""

    synthesis_user = f"""Notes:
{structured_notes}

Write a cohesive summary of approximately {target} words. One or two short paragraphs. No bullet points."""

    messages = [
        {"role": "system", "content": synthesis_system},
        {"role": "user", "content": synthesis_user},
    ]

    return SummarizePrepResult(messages=messages, max_tokens=600, temperature=0.4)

async def process_summarize(text: str, user: User | None, session: AsyncSession) -> dict[str, Any]:
    text = text.strip()
    cfg = get_config()
    if not text:
        raise ValueError("Text is required.")
    
    if len(text.split()) < cfg.min_words:
        raise ValueError(f"Text too short. Minimum {cfg.min_words} words.")

    try:
        summary_text = await summarize(text)
        return {
            "summary": summary_text,
        }
    except httpx.HTTPStatusError as e:
        msg = str(e)
        if "timed out" in msg.lower() or e.response.status_code == 504:
            raise ValueError("Summarization timed out. Try a shorter text.")
        if e.response.status_code == 401:
            raise ValueError("Summarization service misconfigured. Check API key.")
        if e.response.status_code == 429:
            raise ValueError("Rate limit exceeded. Try again in a moment.")
        try:
            body = e.response.json()
            err = body.get("error", body.get("message", msg))
            if isinstance(err, dict):
                err = err.get("message", str(err))
            msg = str(err)
        except Exception:
            pass
        raise ValueError(msg or "Summarization failed.")
    except httpx.RequestError:
        raise ValueError("Cannot reach summarization service. Check your network and API key.")
