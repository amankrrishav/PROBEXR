"""
Summarization: single LLM call (human-like) when an API key is set, or free extractive fallback ($0, no key).

Supports three length modes: brief, standard, detailed.
Returns rich metadata: word counts, compression ratio, reading time, key takeaways.

Architecture: ONE unified LLM call returns both summary + takeaways as structured JSON.
"""
import json
import math
import re
import logging
from typing import Any, Literal
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_config, AppConfig
from app.services.extractive import summarize_extractive
from app.models.user import User

logger = logging.getLogger(__name__)

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
        "structure_guidance": "Distill to the single most critical narrative thread. Every word must earn its place.",
    },
    "standard": {
        "word_ratio": 0.25,
        "min_target": 80,
        "max_target": 300,
        "paragraphs": "one or two short paragraphs",
        "tone": "clear, natural prose",
        "takeaway_count": 5,
        "structure_guidance": "Cover the thesis, key arguments, and conclusion. Preserve causal reasoning and important qualifications.",
    },
    "detailed": {
        "word_ratio": 0.40,
        "min_target": 150,
        "max_target": 600,
        "paragraphs": "three or four paragraphs",
        "tone": "thorough and nuanced, preserving subtlety",
        "takeaway_count": 7,
        "structure_guidance": "Preserve the full argumentative arc: thesis, supporting evidence, counterpoints, qualifications, and implications. Maintain the author's logical flow and nuance.",
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
# Unified prompt builder — the heart of the upgrade
# ---------------------------------------------------------------------------

def _build_unified_prompt(
    text: str,
    target_words: int,
    preset: dict[str, Any],
    length: str,
) -> list[dict[str, str]]:
    """Build a single-call prompt that returns summary + takeaways as JSON."""

    system = f"""You are an expert analyst and communicator. Your task is to read an article and produce TWO things in a SINGLE response:

1. A **summary** written in {preset["tone"]} — approximately {target_words} words, formatted as {preset["paragraphs"]}.
2. Exactly **{preset["takeaway_count"]} key takeaways** — each a single, specific, factual sentence.

## Summary Guidelines
- {preset["structure_guidance"]}
- Write as if explaining to an intelligent colleague who hasn't read the piece.
- Preserve factual accuracy, quantitative claims, and causal relationships exactly as stated.
- Use your own natural phrasing — do NOT copy sentences verbatim from the source.
- Maintain a formal but readable tone. No bullet points in the summary.
- Include specific names, numbers, and evidence when they are central to the argument.

## Takeaway Guidelines
- Each takeaway must be a standalone, self-contained sentence a reader can understand without context.
- Prioritize: (1) the core thesis, (2) surprising or counterintuitive findings, (3) quantitative evidence, (4) practical implications.
- Avoid vague generalities like "The article discusses..." — be concrete and specific.

## Anti-Hallucination Rules
- Use ONLY information present in the provided text. Do NOT add outside knowledge, speculation, or inferences beyond what the text states.
- If the text is ambiguous on a point, reflect that ambiguity rather than resolving it.

## Output Format
Respond with ONLY a valid JSON object — no markdown fences, no commentary, no preamble:
{{"summary": "your summary here", "key_takeaways": ["takeaway 1", "takeaway 2", ...]}}"""

    user = f"Article to summarize:\n\n{text}"

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _parse_llm_json(raw: str) -> dict[str, Any]:
    """Robustly parse the LLM's JSON response, handling common format issues."""
    cleaned = raw.strip()

    # Strip markdown code fences if present
    if cleaned.startswith("```"):
        cleaned = re.sub(r'^```\w*\n?', '', cleaned)
        cleaned = re.sub(r'\n?```$', '', cleaned)
        cleaned = cleaned.strip()

    # Try direct parse
    try:
        result = json.loads(cleaned)
        if isinstance(result, dict) and "summary" in result:
            return result
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the response
    match = re.search(r'\{[^{}]*"summary"\s*:\s*"[^"]*"[^{}]*\}', cleaned, re.DOTALL)
    if not match:
        # More permissive: find any JSON object
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)

    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, dict) and "summary" in result:
                return result
        except json.JSONDecodeError:
            pass

    # Last resort: treat entire response as summary text
    logger.warning("Could not parse LLM response as JSON, using raw text as summary")
    return {"summary": cleaned, "key_takeaways": []}


# ---------------------------------------------------------------------------
# Core summarize function — SINGLE LLM CALL
# ---------------------------------------------------------------------------

async def summarize(text: str, length: str = "standard") -> dict[str, Any]:
    """
    Summarize text and extract takeaways in a single LLM call.

    Returns dict with 'summary' (str) and 'key_takeaways' (list[str]).
    Falls back to extractive if no LLM provider configured.
    """
    cfg = get_config()
    text = _clean_text(text)
    words = text.split()
    if len(words) < cfg.min_words:
        raise ValueError(f"Text too short. Minimum {cfg.min_words} words.")

    if not cfg.has_llm_provider:
        summary = summarize_extractive(
            text,
            min_words=cfg.min_words,
            target_min=cfg.target_min_words,
            target_max=cfg.target_max_words,
        )
        preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])
        takeaways = _extract_takeaways_from_extractive(summary, count=preset["takeaway_count"])
        return {"summary": summary, "key_takeaways": takeaways}

    llm = _get_llm()
    original_word_count = len(words)
    target = _target_words(original_word_count, cfg, length)
    preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])

    messages = _build_unified_prompt(text, target, preset, length)

    # Single LLM call — summary + takeaways together
    raw = await llm.chat_completion(
        messages,
        max_tokens=max(800, target * 4),
        temperature=0.3,
    )

    if not raw.strip():
        raise ValueError("Could not generate summary. Try a different article.")

    result = _parse_llm_json(raw)
    summary = result.get("summary", "").strip()
    takeaways = result.get("key_takeaways", [])

    if not summary:
        raise ValueError("Summary could not be generated.")

    # Ensure takeaways are clean strings
    takeaways = [str(t).strip() for t in takeaways if str(t).strip()][:preset["takeaway_count"]]

    return {"summary": summary, "key_takeaways": takeaways}


# ---------------------------------------------------------------------------
# SummarizePrepResult — for streaming
# ---------------------------------------------------------------------------

class SummarizePrepResult:
    """Result of prepare_summarize_messages — either extractive or LLM messages ready to stream."""
    def __init__(
        self,
        *,
        extractive_result: str | None = None,
        extractive_takeaways: list[str] | None = None,
        messages: list[dict[str, str]] | None = None,
        max_tokens: int = 800,
        temperature: float = 0.3,
        original_text: str = "",
        length: str = "standard",
        takeaway_count: int = 5,
    ):
        self.extractive_result = extractive_result
        self.extractive_takeaways = extractive_takeaways
        self.messages = messages
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.original_text = original_text
        self.length = length
        self.takeaway_count = takeaway_count

    @property
    def is_extractive(self) -> bool:
        return self.extractive_result is not None


async def prepare_summarize_messages(text: str, length: str = "standard") -> SummarizePrepResult:
    """
    Validate and prepare for summarization.

    Returns a SummarizePrepResult:
      - If no LLM provider: contains extractive_result + extractive_takeaways
      - If LLM available: returns unified prompt messages (NO blocking LLM call!)

    Raises ValueError on validation failure.
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
        preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])
        takeaways = _extract_takeaways_from_extractive(result, count=preset["takeaway_count"])
        return SummarizePrepResult(
            extractive_result=result,
            extractive_takeaways=takeaways,
            original_text=text,
            length=length,
        )

    original_word_count = len(words)
    target = _target_words(original_word_count, cfg, length)
    preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])

    # Build unified prompt — NO blocking LLM call here!
    messages = _build_unified_prompt(text, target, preset, length)

    return SummarizePrepResult(
        messages=messages,
        max_tokens=max(800, target * 4),
        temperature=0.3,
        original_text=text,
        length=length,
        takeaway_count=preset["takeaway_count"],
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

    try:
        # Single call returns both summary and takeaways
        result = await summarize(text, length=length)
        summary_text = result["summary"]
        takeaways = result["key_takeaways"]

        # Compute metadata
        meta = _compute_metadata(text, summary_text)

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
