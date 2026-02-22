"""
Free extractive summarizer — no API key, no cost.
Uses sentence position + length heuristics. Quality is lower than LLM but $0 and works everywhere.
"""
import re


def _clean_text(text: str) -> str:
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _sentences(text: str) -> list[str]:
    # Split on sentence boundaries, keep the delimiter attached to the previous part
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _target_word_count(num_words: int, min_w: int = 80, max_w: int = 300) -> int:
    target = max(min_w, int(num_words * 0.25))
    return min(target, max_w)


def summarize_extractive(text: str, min_words: int = 30, target_min: int = 80, target_max: int = 300) -> str:
    """
    Extract key sentences by position and length. No API, no cost.
    Returns a single paragraph summary.
    """
    text = _clean_text(text)
    words = text.split()
    if len(words) < min_words:
        raise ValueError(f"Text too short. Minimum {min_words} words.")

    sentences = _sentences(text)
    if not sentences:
        return text[:500]  # fallback: first 500 chars

    target_words = _target_word_count(len(words), target_min, target_max)

    # Score: prefer early sentences (intro/context) and mid-late (conclusions), avoid very short
    n = len(sentences)
    scored = []
    for i, s in enumerate(sentences):
        w = len(s.split())
        if w < 3:
            score = -1
        else:
            # Slight boost for first 2 and last 2 sentences; mild penalty for very long
            pos = i / max(n - 1, 1)
            pos_score = 1.0
            if i < 2:
                pos_score = 1.3
            elif i >= n - 2:
                pos_score = 1.2
            length_score = min(1.5, w / 15)  # prefer 10–20 word sentences
            score = pos_score * length_score
        scored.append((score, i, s))

    scored.sort(key=lambda x: (-x[0], x[1]))

    # Take sentences in original order until we reach target words
    chosen = [(i, s) for _, i, s in scored]
    chosen.sort(key=lambda x: x[0])
    result_words = 0
    out = []
    for _, s in chosen:
        if result_words >= target_words:
            break
        out.append(s)
        result_words += len(s.split())

    summary = " ".join(out)
    return summary.strip() if summary else text[:500]
