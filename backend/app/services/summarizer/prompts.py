"""
Summarizer Prompts — Clean, mode-aware prompt templates.

Key design: NO JSON separator in the output. The LLM produces ONLY the summary.
All metadata (entities, compression ratio, etc.) is computed in intelligence.py.
This prevents the #1 bug: free-tier LLMs leaking separator/JSON into the visible stream.
"""
from typing import Any


# ── Mode-specific format instructions ──────────────────────────────────────

_MODE_INSTRUCTIONS = {
    "paragraph": (
        "Write the summary as flowing, natural prose paragraphs. "
        "Do NOT use bullet points, lists, or headings."
    ),
    "bullets": (
        "Write the summary as a clean bullet-point list. "
        "Use '•' as the bullet prefix. Each point should be 8–20 words. "
        "No introductory sentence — go straight into bullets."
    ),
    "key_sentences": (
        "Extract the most important original sentences directly from the source text. "
        "Do NOT rephrase — use the author's exact words. "
        "Present them as a numbered list (1., 2., 3., etc.)."
    ),
    "abstract": (
        "Write an academic-style abstract. Follow this structure: "
        "Background → Methods/Argument → Findings → Conclusion. "
        "Use formal academic language. Target ~150 words."
    ),
    "tldr": (
        "Write an ultra-short TL;DR of 1–2 sentences maximum. "
        "Capture the single most important takeaway. Be punchy and direct."
    ),
    "outline": (
        "Write a hierarchical outline with main topic headings (use ## for headings) "
        "and sub-bullets (use - for sub-points) for supporting details. "
        "This should read like a structured table of contents with detail."
    ),
    "executive": (
        "Write a business-style executive summary with exactly three labeled sections:\n"
        "**Overview:** (1–2 sentences of context)\n"
        "**Key Points:** (3–5 bullet points with the core findings)\n"
        "**Bottom Line:** (1 sentence actionable takeaway)"
    ),
}

# ── Tone instructions  ────────────────────────────────────────────────────

_TONE_INSTRUCTIONS = {
    "neutral": "Use clear, balanced, professional language.",
    "formal": "Use formal, academic language. Avoid contractions and colloquialisms.",
    "casual": "Use simple, conversational language. Short sentences. Easy to read.",
    "creative": "Use engaging, vivid language. Make it interesting to read. Use strong verbs.",
    "technical": "Use precise, technical language. Preserve domain-specific terminology.",
}


def build_unified_prompt(
    text: str,
    target_words: int,
    preset: dict[str, Any],
    *,
    mode: str = "paragraph",
    tone: str = "neutral",
    keywords: list[str] | None = None,
) -> list[dict[str, str]]:
    """
    Build a prompt that produces ONLY the summary text — no JSON, no metadata.
    The LLM's job is summarization. Everything else is computed in code.
    """
    mode_instruction = _MODE_INSTRUCTIONS.get(mode, _MODE_INSTRUCTIONS["paragraph"])
    tone_instruction = _TONE_INSTRUCTIONS.get(tone, _TONE_INSTRUCTIONS["neutral"])

    keyword_block = ""
    if keywords:
        kw_str = ", ".join(keywords[:5])
        keyword_block = f"\n- **Focus Keywords**: Emphasize themes related to: {kw_str}"

    system = f"""You are an expert summarization engine. You produce high-quality, human-like summaries that are accurate, coherent, and preserve the key ideas of the original.

## Rules
1. Target approximately {target_words} words.
2. NEVER hallucinate facts not in the source text.
3. NEVER add opinions unless the tone explicitly calls for it.
4. NEVER use meta-discourse like "The article discusses", "In this text", "The author argues".
5. Every sentence must carry information — no filler.
6. Produce ONLY the summary. No preamble, no commentary, no titles, no labels like "Summary:".

## Output Format
{mode_instruction}

## Tone
{tone_instruction}{keyword_block}"""

    user = f"Summarize the following text:\n\n{text}"

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_takeaway_prompt(summary: str, count: int = 5) -> list[dict[str, str]]:
    """
    Build a lightweight prompt to extract key takeaways from a completed summary.
    This is a second, cheap call — avoids polluting the main summary with JSON.
    """
    system = f"""Extract exactly {count} key takeaways from the summary below.
Format: one takeaway per line, prefixed with "• ".
Each takeaway should be 10–20 words — specific and actionable.
Output ONLY the bullet points. Nothing else."""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": summary},
    ]


def build_reduce_prompt(
    chunk_summaries: list[str],
    target_words: int,
    preset: dict[str, Any],
    *,
    mode: str = "paragraph",
    tone: str = "neutral",
    keywords: list[str] | None = None,
) -> list[dict[str, str]]:
    """Prompt for the 'Reduce' phase of map-reduce synthesis."""
    combined = "\n\n---\n\n".join(chunk_summaries)
    mode_instruction = _MODE_INSTRUCTIONS.get(mode, _MODE_INSTRUCTIONS["paragraph"])
    tone_instruction = _TONE_INSTRUCTIONS.get(tone, _TONE_INSTRUCTIONS["neutral"])

    keyword_block = ""
    if keywords:
        kw_str = ", ".join(keywords[:5])
        keyword_block = f"\n- **Focus Keywords**: Emphasize themes related to: {kw_str}"

    system = f"""You are a synthesis expert. Merge the provided section summaries into a single, seamless narrative of approximately {target_words} words.

## Rules
1. The output must read as one unified piece — not a list of summaries stitched together.
2. Aggressively de-duplicate overlapping points.
3. Prioritize the most important information.
4. Produce ONLY the merged summary. No preamble, no commentary.

## Output Format
{mode_instruction}

## Tone
{tone_instruction}{keyword_block}"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Section summaries to merge:\n\n{combined}"},
    ]
