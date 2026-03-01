"""
Summarization: LLM (human-like) when an API key is set, or free extractive fallback ($0, no key).

Supports three length modes: brief, standard, detailed.
Returns rich metadata: word counts, compression ratio, reading time, key takeaways.
"""
import math
import re
from typing import Any, Literal
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


# ---------------------------------------------------------------------------
# Length presets
# ---------------------------------------------------------------------------

LENGTH_PRESETS = {
    "brief": {
        "word_ratio": 0.12,
        "min_target": 40,
        "max_target": 120,
        "paragraphs": "one short paragraph",
        "tone": "extremely concise, no filler",
        "takeaway_count": 3,
    },
    "standard": {
        "word_ratio": 0.25,
        "min_target": 80,
        "max_target": 300,
        "paragraphs": "one or two short paragraphs",
        "tone": "clear, natural prose",
        "takeaway_count": 5,
    },
    "detailed": {
        "word_ratio": 0.40,
        "min_target": 150,
        "max_target": 600,
        "paragraphs": "three or four paragraphs",
        "tone": "thorough and nuanced, preserving subtlety",
        "takeaway_count": 7,
    },
}


def _target_words(original_word_count: int, cfg: AppConfig, length: str = "standard") -> int:
    preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])
    base = max(preset["min_target"], int(original_word_count * preset["word_ratio"]))
    return min(base, preset["max_target"])


def _compute_metadata(original_text: str, summary_text: str) -> dict[str, Any]:
    """Compute word counts, compression ratio, and reading time."""
    original_wc = len(original_text.split())
    summary_wc = len(summary_text.split())
    compression = round((1 - summary_wc / max(original_wc, 1)) * 100, 1)
    # Average reading speed: ~200 words/min
    reading_time_seconds = max(1, round(summary_wc / 200 * 60))
    return {
        "original_word_count": original_wc,
        "summary_word_count": summary_wc,
        "compression_ratio": compression,
        "reading_time_seconds": reading_time_seconds,
    }


def _extract_takeaways_from_extractive(summary: str, count: int = 3) -> list[str]:
    """Derive takeaways from extractive summary by splitting sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', summary.strip())
    return [s.strip() for s in sentences[:count] if s.strip()]


# ---------------------------------------------------------------------------
# Core summarize function
# ---------------------------------------------------------------------------

async def summarize(text: str, length: str = "standard") -> str:
    cfg = get_config()
    text = _clean_text(text)
    words = text.split()
    if len(words) < cfg.min_words:
        raise ValueError(f"Text too short. Minimum {cfg.min_words} words.")

    if not cfg.has_llm_provider:
        return summarize_extractive(
            text,
            min_words=cfg.min_words,
            target_min=cfg.target_min_words,
            target_max=cfg.target_max_words,
        )

    llm = _get_llm()
    original_word_count = len(words)
    target_words = _target_words(original_word_count, cfg, length)
    preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])

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

    synthesis_system = f"""You are a skilled explainer. Using only the notes provided, write a short summary as if you understood the topic and are explaining it to a colleague.
Write in {preset["tone"]}. Preserve important facts and nuance. Do not copy phrases from the notes verbatim—use your own words. Keep a formal but readable tone."""

    synthesis_user = f"""Notes:
{structured_notes}

Write a cohesive summary of approximately {target_words} words. {preset["paragraphs"]}. No bullet points."""

    final_summary = await llm.chat_completion(
        [
            {"role": "system", "content": synthesis_system},
            {"role": "user", "content": synthesis_user},
        ],
        max_tokens=max(600, target_words * 3),
        temperature=0.4,
    )

    return final_summary.strip() or "Summary could not be generated."


# ---------------------------------------------------------------------------
# Key takeaways (LLM)
# ---------------------------------------------------------------------------

async def _extract_takeaways_llm(text: str, count: int = 5) -> list[str]:
    """Use the LLM to extract key takeaways as bullet points."""
    llm = _get_llm()
    prompt = f"""Extract exactly {count} key takeaways from this text. Each takeaway should be a single concise sentence.
Return ONLY a JSON array of strings, nothing else. Example: ["First point", "Second point"]

Text:
{text[:6000]}"""

    try:
        reply = await llm.chat_completion(
            [{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.2,
        )
        # Parse JSON array
        import json
        cleaned = reply.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r'^```\w*\n?', '', cleaned)
            cleaned = re.sub(r'\n?```$', '', cleaned)
        takeaways = json.loads(cleaned.strip())
        if isinstance(takeaways, list):
            return [str(t).strip() for t in takeaways[:count]]
    except Exception:
        pass
    return []


# ---------------------------------------------------------------------------
# SummarizePrepResult — for streaming
# ---------------------------------------------------------------------------

class SummarizePrepResult:
    """Result of prepare_summarize_messages — either extractive or LLM messages ready to stream."""
    def __init__(
        self,
        *,
        extractive_result: str | None = None,
        messages: list[dict[str, str]] | None = None,
        max_tokens: int = 600,
        temperature: float = 0.4,
        original_text: str = "",
        length: str = "standard",
    ):
        self.extractive_result = extractive_result
        self.messages = messages
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.original_text = original_text
        self.length = length

    @property
    def is_extractive(self) -> bool:
        return self.extractive_result is not None


async def prepare_summarize_messages(text: str, length: str = "standard") -> SummarizePrepResult:
    """
    Validate and prepare for summarization.

    Returns a SummarizePrepResult:
      - If no LLM provider: contains extractive_result
      - If LLM available: runs Stage 1 extraction, returns Stage 2 synthesis messages.

    Raises ValueError on validation failure or extraction failure.
    """
    cfg = get_config()
    text = _clean_text(text)
    words = text.split()

    if len(words) < cfg.min_words:
        raise ValueError(f"Text too short. Minimum {cfg.min_words} words.")

    if not cfg.has_llm_provider:
        result = summarize_extractive(
            text,
            min_words=cfg.min_words,
            target_min=cfg.target_min_words,
            target_max=cfg.target_max_words,
        )
        return SummarizePrepResult(extractive_result=result, original_text=text, length=length)

    llm = _get_llm()
    original_word_count = len(words)
    target = _target_words(original_word_count, cfg, length)
    preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])

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

    synthesis_system = f"""You are a skilled explainer. Using only the notes provided, write a short summary as if you understood the topic and are explaining it to a colleague.
Write in {preset["tone"]}. Preserve important facts and nuance. Do not copy phrases from the notes verbatim—use your own words. Keep a formal but readable tone."""

    synthesis_user = f"""Notes:
{structured_notes}

Write a cohesive summary of approximately {target} words. {preset["paragraphs"]}. No bullet points."""

    messages = [
        {"role": "system", "content": synthesis_system},
        {"role": "user", "content": synthesis_user},
    ]

    return SummarizePrepResult(
        messages=messages,
        max_tokens=max(600, target * 3),
        temperature=0.4,
        original_text=text,
        length=length,
    )


# ---------------------------------------------------------------------------
# process_summarize — called by non-streaming endpoint
# ---------------------------------------------------------------------------

async def process_summarize(text: str, user: User | None, session: AsyncSession, length: str = "standard") -> dict[str, Any]:
    text = text.strip()
    cfg = get_config()
    if not text:
        raise ValueError("Text is required.")

    if len(text.split()) < cfg.min_words:
        raise ValueError(f"Text too short. Minimum {cfg.min_words} words.")

    preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])

    try:
        summary_text = await summarize(text, length=length)

        # Compute metadata
        meta = _compute_metadata(text, summary_text)

        # Key takeaways
        if cfg.has_llm_provider:
            takeaways = await _extract_takeaways_llm(text, count=preset["takeaway_count"])
        else:
            takeaways = _extract_takeaways_from_extractive(summary_text, count=preset["takeaway_count"])

        return {
            "summary": summary_text,
            "key_takeaways": takeaways,
            "quality": "full" if cfg.has_llm_provider else "extractive",
            "length": length,
            **meta,
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
