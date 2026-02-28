"""
Summarization: LLM (human-like) when an API key is set, or free extractive fallback ($0, no key).
Reduced quality uses the simpler extractive summarizer even when an LLM is configured.
"""
import re
from typing import Literal, Any, Tuple
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_config, AppConfig
from app.services.extractive import summarize_extractive
from app.services.subscription import evaluate_summary_quality
from app.models.user import User

# Lazy import so extractive path works without httpx when no key
_llm = None


Quality = Literal["full", "reduced"]


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
    Compute target word count for full-quality LLM summaries.
    """
    base = max(cfg.target_min_words, int(original_word_count * 0.25))
    return min(base, cfg.target_max_words)


async def summarize(text: str, quality: Quality = "full") -> str:
    """
    If an API key is set and quality=='full': use LLM (human-like, two-stage).
    If quality=='reduced' or no key: use extractive fallback ($0, no API, lower quality).
    """
    cfg = get_config()
    text = _clean_text(text)
    words = text.split()
    if len(words) < cfg.min_words:
        raise ValueError(f"Text too short. Minimum {cfg.min_words} words.")

    # Extractive path: always used when quality is reduced, or when no LLM provider exists.
    if quality == "reduced" or not cfg.has_llm_provider:
        return summarize_extractive(
            text,
            min_words=cfg.min_words,
            target_min=cfg.target_min_words,
            target_max=cfg.target_max_words,
        )

    # Paid path (or free-tier API): use LLM for full-quality summaries.
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

async def process_summarize(text: str, user: User | None, session: AsyncSession) -> dict[str, Any]:
    text = text.strip()
    cfg = get_config()
    if not text:
        raise ValueError("Text is required.")
    
    if len(text.split()) < cfg.min_words:
        raise ValueError(f"Text too short. Minimum {cfg.min_words} words.")

    try:
        quality, usage_today, limit = await evaluate_summary_quality(user, session)
        summary_text = await summarize(text, quality=quality)
        return {
            "summary": summary_text,
            "quality": quality,
            "usage_today": usage_today,
            "limit": limit,
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
