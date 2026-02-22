"""
Summarization: LLM (human-like) when an API key is set, or free extractive fallback ($0, no key).
"""
import re
from app.config import get_config
from app.services.extractive import summarize_extractive

# Lazy import so extractive path works without httpx when no key
_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        from app.services import llm as m
        _llm = m
    return _llm


def _clean_text(text: str) -> str:
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _target_words(original_word_count: int, cfg) -> int:
    target = max(cfg.target_min_words, int(original_word_count * 0.25))
    return min(target, cfg.target_max_words)


def _has_llm_provider(cfg) -> bool:
    return bool(cfg.groq_api_key or cfg.openai_api_key or cfg.openrouter_api_key)


async def summarize(text: str) -> str:
    """
    If an API key is set: use LLM (human-like, two-stage). Free tier = $0 (Groq/OpenRouter).
    If no key: use extractive fallback ($0, no API, lower quality).
    """
    cfg = get_config()
    text = _clean_text(text)
    words = text.split()
    if len(words) < cfg.min_words:
        raise ValueError(f"Text too short. Minimum {cfg.min_words} words.")

    # Free path: no API key → extractive only ($0)
    if not _has_llm_provider(cfg):
        return summarize_extractive(
            text,
            min_words=cfg.min_words,
            target_min=cfg.target_min_words,
            target_max=cfg.target_max_words,
        )

    # Paid path (or free-tier API): use LLM
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
