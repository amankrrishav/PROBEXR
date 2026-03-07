"""
Summarization: single LLM call (human-like) when an API key is set, or free
TF-IDF extractive fallback ($0, no key).

Supports three length modes: brief, standard, detailed.
Returns rich metadata: word counts, compression ratio, reading time, key takeaways,
content type detection, readability scoring, and notable quote extraction.

Architecture: ONE unified LLM call returns both summary + takeaways as structured JSON.

Upgrades:
  - Chain-of-density inspired prompt engineering with domain-adaptive tone
  - Smart text preprocessing: boilerplate removal, unicode normalization
  - Map-reduce chunking for long articles (>3000 words)
  - Response validation: length checks, auto-retry on garbage
  - In-memory hash cache to skip re-summarization of identical text
  - Stronger anti-hallucination guardrails
  - Content-type auto-detection (news, academic, technical, opinion, general)
  - Flesch-Kincaid readability scoring with human labels
  - Notable quote extraction from source text
  - Content-type-adaptive prompt tuning
"""
import hashlib
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


# ---------------------------------------------------------------------------
# In-memory cache — avoids re-summarizing identical text within process life
# ---------------------------------------------------------------------------

_cache: dict[str, dict[str, Any]] = {}
_MAX_CACHE_SIZE = 200


def _cache_key(text: str, length: str) -> str:
    return hashlib.sha256(f"{length}::{text}".encode()).hexdigest()


def _cache_get(text: str, length: str) -> dict[str, Any] | None:
    return _cache.get(_cache_key(text, length))


def _cache_set(text: str, length: str, result: dict[str, Any]) -> None:
    if len(_cache) >= _MAX_CACHE_SIZE:
        # Evict oldest quarter
        keys = list(_cache.keys())
        for k in keys[:_MAX_CACHE_SIZE // 4]:
            _cache.pop(k, None)
    _cache[_cache_key(text, length)] = result


# ---------------------------------------------------------------------------
# Text preprocessing
# ---------------------------------------------------------------------------

# Boilerplate patterns commonly found in scraped web articles
_BOILERPLATE_RE = [
    re.compile(r"(?i)\b(cookie|privacy)\s+(policy|notice|settings?)\b.*$", re.MULTILINE),
    re.compile(r"(?i)^\s*(advertisement|sponsored|promoted|ad)\s*$", re.MULTILINE),
    re.compile(r"(?i)^\s*(share|follow|like)\s+(this|us|on)\b.*$", re.MULTILINE),
    re.compile(r"(?i)^\s*(photo|image|video|credit|source)\s*:.*$", re.MULTILINE),
    re.compile(r"(?i)^\s*©.*$", re.MULTILINE),
    re.compile(r"(?i)\ball\s+rights\s+reserved\b.*$", re.MULTILINE),
    re.compile(r"(?i)^\s*(click|tap)\s+here\b.*$", re.MULTILINE),
    re.compile(r"(?i)\b(sign\s*up|subscribe|newsletter|log\s*in)\s+(for|to|now)\b.*$", re.MULTILINE),
    re.compile(r"(?i)\bread\s+more\s*[:\.]?\s*$", re.MULTILINE),
    # Additional boilerplate
    re.compile(r"(?i)^\s*(related\s+articles?|you\s+may\s+also\s+like|recommended)\s*[:\.]?.*$", re.MULTILINE),
    re.compile(r"(?i)^\s*(table\s+of\s+contents?)\s*$", re.MULTILINE),
    re.compile(r"(?i)^\s*(leave\s+a\s+comment|comments?\s+section).*$", re.MULTILINE),
    re.compile(r"(?i)^\s*(last\s+updated|published|modified)\s*:?\s*\d.*$", re.MULTILINE),
    re.compile(r"(?i)^\s*tags?\s*:.*$", re.MULTILINE),
    re.compile(r"(?i)\b(accept\s+(all\s+)?cookies?)\b.*$", re.MULTILINE),
    re.compile(r"(?i)\b(we\s+use\s+cookies?)\b.*$", re.MULTILINE),
]


def _clean_text(text: str) -> str:
    """Aggressively clean text: remove boilerplate, normalize unicode, collapse whitespace."""
    # Remove citation markers [1], [2], etc.
    text = re.sub(r"\[\d+\]", "", text)

    # Normalize unicode
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", " — ")
    text = text.replace("\u00a0", " ")  # non-breaking space
    text = text.replace("\u200b", "")   # zero-width space
    text = text.replace("\u2026", "...")  # ellipsis
    text = text.replace("\u200e", "")   # left-to-right mark
    text = text.replace("\u200f", "")   # right-to-left mark
    text = text.replace("\ufeff", "")   # BOM

    # Remove image alt text artifacts
    text = re.sub(r"\[(?:image|img|photo|figure|alt)\s*:?[^\]]*\]", "", text, flags=re.IGNORECASE)

    # Remove boilerplate patterns
    for pattern in _BOILERPLATE_RE:
        text = pattern.sub("", text)

    # Collapse multiple newlines into paragraph breaks, then to spaces
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\n", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Content-type detection
# ---------------------------------------------------------------------------

_ACADEMIC_SIGNALS = re.compile(
    r"(?i)\b(abstract|methodology|hypothesis|empirical|peer[- ]review|findings|p[- ]?value"
    r"|statistical(?:ly)?\s+significant|literature\s+review|et\s+al\.?|doi:|arxiv"
    r"|journal\s+of|proceedings|meta[- ]analysis|regression|controlled\s+trial)\b"
)
_NEWS_SIGNALS = re.compile(
    r"(?i)\b(reuters|associated\s+press|AP|AFP|reported\s+(?:on|that|by)"
    r"|press\s+release|breaking\s+news|correspondent|spokesperson"
    r"|according\s+to\s+(?:a\s+)?(?:statement|official|source)|announced\s+(?:on|today|that))\b"
)
_TECH_SIGNALS = re.compile(
    r"(?i)\b(api|sdk|framework|deploy(?:ment)?|(?:micro)?service|kubernetes|docker"
    r"|repository|open[- ]?source|backend|frontend|algorithm|benchmark"
    r"|latency|throughput|scalab(?:le|ility)|machine\s+learning|neural\s+net(?:work)?)\b"
)
_OPINION_SIGNALS = re.compile(
    r"(?i)\b(i\s+(?:believe|think|argue|contend)|in\s+my\s+(?:view|opinion|experience)"
    r"|(?:we|i)\s+should|it\s+(?:seems|appears)\s+(?:to me|that)|editorial|op[- ]?ed"
    r"|commentary|my\s+take|i\s+(?:strongly|firmly))\b"
)


def _detect_content_type(text: str) -> str:
    """Classify content as: academic, news, technical, opinion, or general."""
    academic = len(_ACADEMIC_SIGNALS.findall(text))
    news = len(_NEWS_SIGNALS.findall(text))
    tech = len(_TECH_SIGNALS.findall(text))
    opinion = len(_OPINION_SIGNALS.findall(text))

    scores = {
        "academic": academic * 2,  # academic signals are stronger markers
        "news": news,
        "technical": tech,
        "opinion": opinion,
    }

    best = max(list(scores.keys()), key=lambda k: scores[k])
    # Require minimum signal strength to classify — otherwise "general"
    if scores[best] < 3:
        return "general"
    return best


_CONTENT_TYPE_TONE = {
    "academic": "precise and scholarly — preserve methodological rigor, hedge language, and qualification",
    "news": "factual and direct — lead with the who/what/where/when, then context and implications",
    "technical": "clear and practical — focus on what it does, how it works, and why it matters to practitioners",
    "opinion": "balanced — present the author's argument fairly, note the evidence cited, and capture the rhetorical stance",
    "general": "clear, natural prose — like a senior analyst briefing a busy executive",
}


# ---------------------------------------------------------------------------
# Readability scoring (Flesch-Kincaid)
# ---------------------------------------------------------------------------

def _count_syllables(word: str) -> int:
    """Estimate syllable count using vowel-group heuristic."""
    word = word.lower().rstrip("e")
    if not word:
        return 1
    count = len(re.findall(r"[aeiouy]+", word))
    return max(1, count)


def _readability_score(text: str) -> tuple[float, str]:
    """
    Compute Flesch Reading Ease score and human label.
    Returns (score, label) where higher score = easier to read.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s for s in sentences if s.strip()]
    words = re.findall(r"[a-zA-Z']+", text)

    if not sentences or not words:
        return 50.0, "Average"

    total_sentences = len(sentences)
    total_words = len(words)
    total_syllables = sum(_count_syllables(w) for w in words)

    # Flesch Reading Ease formula
    asl = total_words / total_sentences  # avg sentence length
    asw = total_syllables / total_words  # avg syllables per word
    score = 206.835 - (1.015 * asl) - (84.6 * asw)
    score = round(max(0, min(100, score)), 1)

    # Label
    if score >= 80:
        label = "Very Easy"
    elif score >= 65:
        label = "Easy"
    elif score >= 50:
        label = "Average"
    elif score >= 35:
        label = "Moderate"
    elif score >= 20:
        label = "Difficult"
    else:
        label = "Very Difficult"

    return score, label


# ---------------------------------------------------------------------------
# Notable quote extraction
# ---------------------------------------------------------------------------

def _extract_notable_quotes(text: str, max_quotes: int = 3) -> list[str]:
    """
    Extract the most notable direct quotes from the text.
    Looks for quoted text between quotation marks that contains substance.
    """
    # Match both straight and curly quotes
    patterns = [
        re.compile(r'["\u201c]([^"\u201d]{20,200})["\u201d]'),
    ]

    quotes = []
    for pattern in patterns:
        for match in pattern.finditer(text):
            q = match.group(1).strip()
            # Filter out non-substantive quotes
            words = q.split()
            if len(words) < 5:
                continue
            # Skip quotes that look like titles, labels, or UI text
            if q.endswith(":") or q.startswith("http"):
                continue
            quotes.append(q)

    # Deduplicate and take the longest (most substantive) quotes
    seen = set()
    unique = []
    for q in quotes:
        key = q.lower()[:50]
        if key not in seen:
            seen.add(key)
            unique.append(q)

    # Sort by length descending (longer quotes tend to be more substantive)
    unique.sort(key=len, reverse=True)
    return unique[:max_quotes]


# ---------------------------------------------------------------------------
# Length presets — tuned for quality
# ---------------------------------------------------------------------------

LENGTH_PRESETS = {
    "brief": {
        "word_ratio": 0.12,
        "min_target": 40,
        "max_target": 120,
        "paragraphs": "one short paragraph",
        "tone": "extremely concise, zero filler — every word must earn its place",
        "takeaway_count": 3,
        "structure_guidance": (
            "Distill to the single most critical narrative thread. "
            "Capture the thesis and one supporting point. "
            "If a number or statistic is central, include it."
        ),
    },
    "standard": {
        "word_ratio": 0.25,
        "min_target": 80,
        "max_target": 300,
        "paragraphs": "two short paragraphs",
        "tone": "clear, natural prose — like a senior analyst briefing a busy executive",
        "takeaway_count": 5,
        "structure_guidance": (
            "Cover the thesis, 2-3 key arguments or evidence points, and the conclusion. "
            "Preserve causal reasoning, important qualifications, and quantitative claims. "
            "Connect ideas with logical transitions."
        ),
    },
    "detailed": {
        "word_ratio": 0.40,
        "min_target": 150,
        "max_target": 600,
        "paragraphs": "three or four paragraphs",
        "tone": "thorough and nuanced — preserve subtlety, counterpoints, and implications",
        "takeaway_count": 7,
        "structure_guidance": (
            "Preserve the full argumentative arc: thesis, supporting evidence, counterpoints, "
            "qualifications, and implications. Maintain the author's logical flow, nuance, and "
            "rhetorical structure. Include specific names, dates, numbers, and methodology where central."
        ),
    },
}


def _target_words(original_word_count: int, cfg: AppConfig, length: str = "standard") -> int:
    preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])
    base = max(int(str(preset["min_target"])), int(original_word_count * float(str(preset["word_ratio"]))))
    return min(base, int(str(preset["max_target"])))


def _compute_metadata(original_text: str, summary_text: str) -> dict[str, Any]:
    """Compute word counts, compression ratio, reading time, content type, readability, and quotes."""
    original_wc = len(original_text.split())
    summary_wc = len(summary_text.split())
    compression = round((1 - summary_wc / max(original_wc, 1)) * 100, 1)
    reading_time_seconds = max(1, round(summary_wc / 200 * 60))

    # Content-type detection
    content_type = _detect_content_type(original_text)

    # Readability scoring (on the summary, since that's what the user reads)
    readability_score, readability_label = _readability_score(summary_text)

    # Notable quotes from source
    notable_quotes = _extract_notable_quotes(original_text)

    return {
        "original_word_count": original_wc,
        "summary_word_count": summary_wc,
        "compression_ratio": compression,
        "reading_time_seconds": reading_time_seconds,
        "content_type": content_type,
        "readability_score": readability_score,
        "readability_label": readability_label,
        "notable_quotes": notable_quotes,
    }


def _extract_takeaways_from_extractive(summary: str, count: int = 3) -> list[str]:
    """Legacy fallback: derive takeaways by splitting sentences. Used by streaming router."""
    sentences = re.split(r'(?<=[.!?])\s+', summary.strip())
    return [s.strip() for s in sentences[:count] if s.strip()]


# ---------------------------------------------------------------------------
# Chain-of-density inspired prompt — the heart of quality
# ---------------------------------------------------------------------------

def _build_unified_prompt(
    text: str,
    target_words: int,
    preset: dict[str, Any],
    length: str,
    content_type: str = "general",
) -> list[dict[str, str]]:
    """Build a single-call prompt that returns summary + takeaways as structured JSON.
    Adapts tone and strategy based on detected content type."""

    # Adaptive tone based on content type
    tone = _CONTENT_TYPE_TONE.get(content_type, preset["tone"])

    # Content-type-specific instructions
    type_guidance = ""
    if content_type == "academic":
        type_guidance = (
            "\n- Preserve methodology descriptions, sample sizes, and statistical findings."
            "\n- Note limitations and scope acknowledged by the authors."
            "\n- Keep hedge language (\"suggests\", \"may\", \"appears to\") where the original uses it."
        )
    elif content_type == "news":
        type_guidance = (
            "\n- Lead with the core news event (inverted pyramid style)."
            "\n- Include attribution: who said/did/reported what."
            "\n- Note timeline: when events occurred or are expected."
        )
    elif content_type == "technical":
        type_guidance = (
            "\n- Explain how the technology/approach works at a conceptual level."
            "\n- Include performance benchmarks or comparisons if mentioned."
            "\n- Note practical implications: who benefits and how."
        )
    elif content_type == "opinion":
        type_guidance = (
            "\n- Clearly attribute the argument: \"The author argues...\" when presenting contested claims."
            "\n- Distinguish between the author's opinions and cited evidence."
            "\n- Capture the strongest counterarguments the author addresses."
        )

    system = f"""You are an expert analyst and writer. Read the provided article and produce TWO things in a SINGLE response:

1. A **summary** of approximately {target_words} words, formatted as {preset["paragraphs"]}.
2. Exactly **{preset["takeaway_count"]} key takeaways** — each a single, specific, factual sentence.

## Summary Instructions
- Tone: {tone}.
- {preset["structure_guidance"]}
- Write as if explaining to an intelligent colleague who hasn't read the piece.
- Use the "chain of density" approach: start with the most important claim, then layer in supporting details until you reach the target length. Every sentence should add new information.
- Preserve factual accuracy and quantitative claims EXACTLY as stated in the source.
- Use your own natural phrasing — do NOT copy sentences verbatim from the source.
- Include specific names, numbers, dates, and evidence when they are central to the argument.
- Do NOT start with "The article discusses..." or "This piece explores..." — jump straight into the substance.
- No bullet points, no headings, no markdown formatting in the summary.{type_guidance}

## Takeaway Instructions
- Each takeaway must be a standalone, self-contained sentence a reader can understand without context.
- Priority order: (1) core thesis, (2) surprising or counterintuitive findings, (3) quantitative evidence with specific numbers, (4) practical implications.
- Be concrete: "Global EV sales rose 35% to 14 million in 2023" NOT "EV sales increased significantly."
- Avoid vague generalities like "The article discusses..." — state the actual finding or claim.

## Critical Rules
- Use ONLY information present in the provided text. Do NOT add outside knowledge, speculation, or inferences beyond what the text states.
- If the text is ambiguous on a point, reflect that ambiguity rather than resolving it.
- If the article lacks depth or substance, produce a proportionally shorter summary rather than padding with filler.

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

    # Try to find JSON object in the response — handle nested objects
    brace_depth = 0
    start = -1
    for i, ch in enumerate(cleaned):
        if ch == '{':
            if brace_depth == 0:
                start = i
            brace_depth += 1
        elif ch == '}':
            brace_depth -= 1
            if brace_depth == 0 and start >= 0:
                candidate = cleaned[start:i + 1]
                try:
                    result = json.loads(candidate)
                    if isinstance(result, dict) and "summary" in result:
                        return result
                except json.JSONDecodeError:
                    pass
                start = -1

    # Last resort: treat entire response as summary text
    logger.warning("Could not parse LLM response as JSON, using raw text as summary")
    return {"summary": cleaned, "key_takeaways": []}


# ---------------------------------------------------------------------------
# Response validation
# ---------------------------------------------------------------------------

def _validate_summary(summary: str, target_words: int, preset: dict) -> bool:
    """Check that the summary meets minimum quality bars."""
    if not summary or len(summary.strip()) < 20:
        return False
    wc = len(summary.split())
    # Allow generous range: 30% to 250% of target
    if wc < target_words * 0.3 or wc > target_words * 2.5:
        return False
    # Reject if it's mostly the same sentence repeated
    sentences = re.split(r'(?<=[.!?])\s+', summary)
    if len(sentences) >= 3:
        unique = len(set(s.strip().lower() for s in sentences))
        if unique / len(sentences) < 0.5:
            return False
    return True


# ---------------------------------------------------------------------------
# Map-reduce chunking for long articles
# ---------------------------------------------------------------------------

_CHUNK_WORD_LIMIT = 3000  # Chunk if article exceeds this


def _chunk_text(text: str, chunk_size: int = _CHUNK_WORD_LIMIT) -> list[str]:
    """Split long text into overlapping chunks by paragraph boundaries."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    # Split by paragraph-like boundaries (double newline or sentence boundaries)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk: list[str] = []
    current_wc = 0

    for sent in sentences:
        sent_wc = len(sent.split())
        if current_wc + sent_wc > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            # Overlap: keep last 2 sentences for context continuity
            overlap = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk[-1:]
            current_chunk = list(overlap)
            current_wc = sum(len(s.split()) for s in current_chunk)
        current_chunk.append(sent)
        current_wc += sent_wc

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def _build_reduce_prompt(
    chunk_summaries: list[str],
    target_words: int,
    preset: dict[str, Any],
    length: str,
) -> list[dict[str, str]]:
    """Build a reduce prompt to merge chunk summaries into final summary."""
    combined = "\n\n---\n\n".join(
        f"Section {i + 1}:\n{s}" for i, s in enumerate(chunk_summaries)
    )

    system = f"""You are an expert analyst. You are given summaries of different sections of a long article.
Merge them into ONE cohesive summary of approximately {target_words} words, formatted as {preset["paragraphs"]}.
Also extract exactly {preset["takeaway_count"]} key takeaways from the combined content.

Rules:
- Remove redundancy — do not repeat the same point from different sections.
- Preserve the logical flow and narrative arc of the original article.
- Tone: {preset["tone"]}.
- {preset["structure_guidance"]}
- Output ONLY valid JSON: {{"summary": "...", "key_takeaways": ["...", ...]}}"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Section summaries to merge:\n\n{combined}"},
    ]


# ---------------------------------------------------------------------------
# Core summarize function — SINGLE LLM CALL (or map-reduce for long texts)
# ---------------------------------------------------------------------------

async def summarize(text: str, length: str = "standard") -> dict[str, Any]:
    """
    Summarize text and extract takeaways.

    Returns dict with 'summary' (str) and 'key_takeaways' (list[str]).
    Falls back to extractive if no LLM provider configured.
    """
    cfg = get_config()
    text = _clean_text(text)
    words = text.split()
    if len(words) < cfg.min_words:
        raise ValueError(f"Text too short. Minimum {cfg.min_words} words.")

    # Check cache first
    cached = _cache_get(text, length)
    if cached:
        logger.info("Cache hit for summarize request")
        return cached

    if not cfg.has_llm_provider:
        preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])
        ext_result = summarize_extractive(
            text,
            min_words=cfg.min_words,
            target_min=int(str(preset["min_target"])),
            target_max=int(str(preset["max_target"])),
            word_ratio=float(str(preset["word_ratio"])),
            takeaway_count=int(str(preset["takeaway_count"])),
        )
        result = {"summary": ext_result["summary"], "key_takeaways": ext_result["key_takeaways"]}
        _cache_set(text, length, result)
        return result

    llm = _get_llm()
    original_word_count = len(words)
    target = _target_words(original_word_count, cfg, length)
    preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])

    # Detect content type for adaptive prompting
    content_type = _detect_content_type(text)
    logger.info("Content type detected: %s", content_type)

    # Map-reduce for long articles
    chunks = _chunk_text(text)
    if len(chunks) > 1:
        result = await _map_reduce_summarize(chunks, target, preset, length, llm, content_type)
    else:
        result = await _single_call_summarize(text, target, preset, length, llm, content_type=content_type)

    _cache_set(text, length, result)
    return result


async def _single_call_summarize(
    text: str,
    target: int,
    preset: dict[str, Any],
    length: str,
    llm: Any,
    retry: bool = True,
    content_type: str = "general",
) -> dict[str, Any]:
    """Single LLM call summarization with retry on validation failure."""
    messages = _build_unified_prompt(text, target, preset, length, content_type)

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

    # Validation — retry once if quality is poor
    if not _validate_summary(summary, target, preset) and retry:
        logger.warning("Summary failed validation (wc=%d, target=%d). Retrying...",
                        len(summary.split()) if summary else 0, target)
        return await _single_call_summarize(text, target, preset, length, llm, retry=False, content_type=content_type)

    if not summary:
        raise ValueError("Summary could not be generated.")

    takeaways = [str(t).strip() for t in takeaways if str(t).strip()][:preset["takeaway_count"]]

    return {"summary": summary, "key_takeaways": takeaways}


async def _map_reduce_summarize(
    chunks: list[str],
    target: int,
    preset: dict[str, Any],
    length: str,
    llm: Any,
    content_type: str = "general",
) -> dict[str, Any]:
    """Map-reduce: summarize each chunk, then merge summaries."""
    import asyncio

    # Map phase: summarize each chunk concurrently
    chunk_target = max(80, target // len(chunks))

    async def _summarize_chunk(chunk: str) -> str:
        chunk_preset = {**preset, "takeaway_count": 3}
        messages = _build_unified_prompt(chunk, chunk_target, chunk_preset, length, content_type)
        raw = await llm.chat_completion(
            messages,
            max_tokens=max(600, chunk_target * 4),
            temperature=0.3,
        )
        parsed = _parse_llm_json(raw)
        return parsed.get("summary", raw.strip())

    chunk_summaries = await asyncio.gather(*[_summarize_chunk(c) for c in chunks])

    # Reduce phase: merge chunk summaries into final
    reduce_messages = _build_reduce_prompt(
        list(chunk_summaries), target, preset, length
    )
    raw = await llm.chat_completion(
        reduce_messages,
        max_tokens=max(800, target * 4),
        temperature=0.3,
    )

    result = _parse_llm_json(raw)
    summary = result.get("summary", "").strip()
    takeaways = result.get("key_takeaways", [])

    if not summary:
        raise ValueError("Summary could not be generated after merge.")

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
        preset = LENGTH_PRESETS.get(length, LENGTH_PRESETS["standard"])
        ext_result = summarize_extractive(
            text,
            min_words=cfg.min_words,
            target_min=int(str(preset["min_target"])),
            target_max=int(str(preset["max_target"])),
            word_ratio=float(str(preset["word_ratio"])),
            takeaway_count=int(str(preset["takeaway_count"])),
        )
        return SummarizePrepResult(
            extractive_result=ext_result["summary"],
            extractive_takeaways=ext_result["key_takeaways"],
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
        takeaway_count=int(str(preset["takeaway_count"])),
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
        result = await summarize(text, length=length)
        summary_text = result["summary"]
        takeaways = result["key_takeaways"]

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
