"""
Summarizer Core: Orchestration for single-call and map-reduce flows.
Handles synthesis, validation, and metadata integration.

Key change from v1: NO JSON parsing from LLM output. The LLM produces
ONLY clean summary text. Metadata is computed purely in intelligence.py.
Takeaways extracted via a lightweight second LLM call.
"""
import asyncio
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.config import get_config
from app.services.extractive import summarize_extractive
from app.models.user import User
from .prompts import build_unified_prompt, build_reduce_prompt, build_takeaway_prompt
from .intelligence import clean_text, compute_metadata

logger = logging.getLogger(__name__)

# Configuration
_CHUNK_WORD_LIMIT = 3000

LENGTH_PRESETS = {
    "brief": {
        "word_ratio": 0.12, "min_target": 40, "max_target": 120,
        "paragraphs": "one short paragraph",
        "tone": "extremely concise, zero filler", "takeaway_count": 3,
        "structure_guidance": "Distill to the single most critical narrative thread."
    },
    "standard": {
        "word_ratio": 0.25, "min_target": 80, "max_target": 300,
        "paragraphs": "two short paragraphs",
        "tone": "clear, natural prose", "takeaway_count": 5,
        "structure_guidance": "Cover the thesis, 2-3 key arguments, and a conclusion."
    },
    "detailed": {
        "word_ratio": 0.40, "min_target": 150, "max_target": 600,
        "paragraphs": "three or four paragraphs",
        "tone": "thorough and nuanced", "takeaway_count": 7,
        "structure_guidance": "Preserve the full argumentative arc and subtle counterpoints."
    },
}

def _target_words(original_count: int, length: str) -> int:
    preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])
    base = max(int(preset["min_target"]), int(original_count * float(preset["word_ratio"])))
    return min(base, int(preset["max_target"]))


def _parse_takeaways(raw: str) -> list[str]:
    """Parse bullet takeaways from the LLM response."""
    lines = raw.strip().splitlines()
    takeaways = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Strip bullet prefixes
        for prefix in ("•", "-", "*", "·"):
            if line.startswith(prefix):
                line = line[len(prefix):].strip()
                break
        # Strip numbered prefixes like "1.", "2."
        if len(line) > 2 and line[0].isdigit() and line[1] in (".", ")"):
            line = line[2:].strip()
        if line:
            takeaways.append(line)
    return takeaways


async def summarize(
    text: str,
    length: str = "standard",
    mode: str = "paragraph",
    tone: str = "neutral",
    keywords: list[str] | None = None,
) -> dict[str, Any]:
    """Unified entry point for summarization."""
    cfg = get_config()
    text = clean_text(text)
    words = text.split()
    word_count = len(words)

    if word_count < cfg.min_words:
        raise ValueError(f"Text too short. Minimum {cfg.min_words} words.")

    if word_count > cfg.summarize_max_words:
        raise ValueError(
            f"Text too long. Maximum {cfg.summarize_max_words:,} words allowed "
            f"({word_count:,} submitted). Please shorten your input."
        )

    # 1. Extractive Fallback (No LLM)
    if not cfg.has_llm_provider:
        preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])
        ext_res = summarize_extractive(
            text, min_words=cfg.min_words,
            target_min=int(preset["min_target"]), target_max=int(preset["max_target"]),
            word_ratio=float(preset["word_ratio"]), takeaway_count=int(preset["takeaway_count"])
        )
        result = {
            "summary": ext_res["summary"],
            "key_takeaways": ext_res["key_takeaways"],
            "metadata": compute_metadata(text, ext_res["summary"]),
            "quality": "extractive",
            "length": length,
            "mode": mode,
        }
        return result

    # 2. LLM Flow
    target = _target_words(word_count, length)
    preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])

    # Map-Reduce for long text
    if word_count > _CHUNK_WORD_LIMIT:
        result = await _map_reduce_flow(text, target, preset, length, mode=mode, tone=tone, keywords=keywords)
    else:
        result = await _single_call_flow(text, target, preset, length, mode=mode, tone=tone, keywords=keywords)

    result.update({
        "quality": "full",
        "length": length,
        "mode": mode,
    })
    return result


async def process_summarize(
    text: str,
    user: User | None,
    session: AsyncSession,
    length: str = "standard",
    mode: str = "paragraph",
    tone: str = "neutral",
    keywords: list[str] | None = None,
) -> dict[str, Any]:
    """Higher-level wrapper called by the API endpoint. Handles errors and returns final dict."""
    text = text.strip()
    if not text:
        raise ValueError("Text is required.")

    cfg_check = get_config()
    word_count_check = len(text.split())
    if word_count_check > cfg_check.summarize_max_words:
        raise ValueError(
            f"Text too long. Maximum {cfg_check.summarize_max_words:,} words allowed "
            f"({word_count_check:,} submitted). Please shorten your input."
        )

    try:
        res = await summarize(text, length=length, mode=mode, tone=tone, keywords=keywords)
        metadata = res.get("metadata", {})
        return {
            "summary": res["summary"],
            "key_takeaways": res.get("key_takeaways", []),
            "quality": res["quality"],
            "length": res["length"],
            "mode": res.get("mode", "paragraph"),
            **metadata
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise ValueError("Rate limit exceeded. Try again in a moment.")
        if e.response.status_code == 401:
            raise ValueError("Summarization service misconfigured. Check API key.")
        raise ValueError(str(e) or "Summarization failed.")
    except Exception as e:
        if isinstance(e, ValueError): raise e
        logger.exception("Summarization failed unexpectedly")
        raise ValueError("An unexpected error occurred during summarization.")


async def _single_call_flow(
    text: str, target: int, preset: dict, length: str,
    *, mode: str = "paragraph", tone: str = "neutral", keywords: list[str] | None = None,
) -> dict[str, Any]:
    from app.services import llm

    messages = build_unified_prompt(text, target, preset, mode=mode, tone=tone, keywords=keywords)
    summary = await llm.chat_completion(messages, max_tokens=max(1000, target * 4), temperature=0.3)
    summary = summary.strip()

    # Extract takeaways via a lightweight second call (skip for tldr mode — it IS the takeaway)
    takeaway_count = int(preset.get("takeaway_count", 5))
    takeaways = []
    if mode != "tldr" and len(summary.split()) > 30:
        try:
            takeaway_msgs = build_takeaway_prompt(summary, takeaway_count)
            raw_takeaways = await llm.chat_completion(takeaway_msgs, max_tokens=400, temperature=0.2)
            takeaways = _parse_takeaways(raw_takeaways)[:takeaway_count]
        except Exception:
            logger.warning("Takeaway extraction failed, skipping")

    return {
        "summary": summary,
        "key_takeaways": takeaways,
        "metadata": compute_metadata(text, summary),
    }


async def _map_reduce_flow(
    text: str, target: int, preset: dict, length: str,
    *, mode: str = "paragraph", tone: str = "neutral", keywords: list[str] | None = None,
) -> dict[str, Any]:
    from app.services import llm
    import re

    # Map phase: chunk and summarize
    chunks = _chunk_text(text)
    chunk_target = max(100, target // len(chunks))

    async def _map_chunk(c: str) -> str:
        p = {**preset, "takeaway_count": 3}
        msgs = build_unified_prompt(c, chunk_target, p, mode="paragraph", tone=tone, keywords=keywords)
        raw = await llm.chat_completion(msgs, max_tokens=600, temperature=0.3)
        return raw.strip()

    chunk_summaries = await asyncio.gather(*[_map_chunk(c) for c in chunks])

    # Reduce phase: merge and synthesize
    reduce_msgs = build_reduce_prompt(list(chunk_summaries), target, preset, mode=mode, tone=tone, keywords=keywords)
    summary = await llm.chat_completion(reduce_msgs, max_tokens=1000, temperature=0.3)
    summary = summary.strip()

    # Extract takeaways
    takeaway_count = int(preset.get("takeaway_count", 5))
    takeaways = []
    if mode != "tldr" and len(summary.split()) > 30:
        try:
            takeaway_msgs = build_takeaway_prompt(summary, takeaway_count)
            raw_takeaways = await llm.chat_completion(takeaway_msgs, max_tokens=400, temperature=0.2)
            takeaways = _parse_takeaways(raw_takeaways)[:takeaway_count]
        except Exception:
            logger.warning("Takeaway extraction failed in map-reduce, skipping")

    return {
        "summary": summary,
        "key_takeaways": takeaways,
        "metadata": compute_metadata(text, summary),
    }


def _chunk_text(text: str) -> list[str]:
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    curr: list[str] = []
    curr_wc = 0
    for s in sentences:
        swc = len(s.split())
        if curr_wc + swc > _CHUNK_WORD_LIMIT and curr:
            chunks.append(" ".join(curr))
            curr = curr[-3:]
            curr_wc = sum(len(x.split()) for x in curr)
        curr.append(s)
        curr_wc += swc
    if curr: chunks.append(" ".join(curr))
    return chunks


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
        mode: str = "paragraph",
        tone: str = "neutral",
        keywords: list[str] | None = None,
        takeaway_count: int = 5,
    ):
        self.extractive_result = extractive_result
        self.extractive_takeaways = extractive_takeaways
        self.messages = messages
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.original_text = original_text
        self.length = length
        self.mode = mode
        self.tone = tone
        self.keywords = keywords or []
        self.takeaway_count = takeaway_count

    @property
    def is_extractive(self) -> bool:
        return self.extractive_result is not None


async def prepare_summarize_messages(
    text: str,
    length: str = "standard",
    mode: str = "paragraph",
    tone: str = "neutral",
    keywords: list[str] | None = None,
) -> SummarizePrepResult:
    """
    Validate and prepare for summarization without blocking on LLM.
    Used by the streaming router to get the prompt payload.
    """
    cfg = get_config()
    text = clean_text(text)
    words = text.split()
    word_count = len(words)

    if word_count < cfg.min_words:
        raise ValueError(f"Text too short. Minimum {cfg.min_words} words.")

    # 1. Extractive Fallback
    if not cfg.has_llm_provider:
        preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])
        ext_res = summarize_extractive(
            text, min_words=cfg.min_words,
            target_min=int(preset["min_target"]), target_max=int(preset["max_target"]),
            word_ratio=float(preset["word_ratio"]), takeaway_count=int(preset["takeaway_count"])
        )
        return SummarizePrepResult(
            extractive_result=ext_res["summary"],
            extractive_takeaways=ext_res["key_takeaways"],
            original_text=text,
            length=length,
            mode=mode,
            tone=tone,
            keywords=keywords,
            takeaway_count=int(preset["takeaway_count"]),
        )

    # 2. LLM Path
    target = _target_words(word_count, length)
    preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])
    messages = build_unified_prompt(text, target, preset, mode=mode, tone=tone, keywords=keywords)

    return SummarizePrepResult(
        messages=messages,
        max_tokens=max(1000, target * 4),
        temperature=0.3,
        original_text=text,
        length=length,
        mode=mode,
        tone=tone,
        keywords=keywords,
        takeaway_count=int(preset["takeaway_count"]),
    )