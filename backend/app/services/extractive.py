"""
Advanced extractive summarizer — no API key, no cost.

Uses TF-IDF weighted sentence scoring with MMR diversity selection.
Significantly better quality than basic position/length heuristics.
"""
import math
import re
from collections import Counter


# ---------------------------------------------------------------------------
# Text cleaning & sentence segmentation
# ---------------------------------------------------------------------------

_ABBREVIATIONS = frozenset([
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc",
    "inc", "ltd", "co", "corp", "dept", "univ", "govt", "approx",
    "fig", "vol", "no", "jan", "feb", "mar", "apr", "jun", "jul",
    "aug", "sep", "oct", "nov", "dec", "al", "e.g", "i.e",
])

# Boilerplate patterns commonly found in scraped web articles
_BOILERPLATE_PATTERNS = [
    re.compile(r"(?i)\b(cookie|privacy)\s+(policy|notice|settings?)\b"),
    re.compile(r"(?i)\b(sign\s+up|subscribe|newsletter|log\s*in|register)\s+(for|to|now)\b"),
    re.compile(r"(?i)\bshare\s+(this|on)\s+(article|story|facebook|twitter|linkedin)\b"),
    re.compile(r"(?i)^(advertisement|sponsored|promoted|ad)\s*$"),
    re.compile(r"(?i)\bread\s+more\s*[:\.]?\s*$"),
    re.compile(r"(?i)^\s*(photo|image|video|credit|source)\s*:"),
    re.compile(r"(?i)\ball\s+rights\s+reserved\b"),
    re.compile(r"(?i)^\s*©"),
    re.compile(r"(?i)^\s*(follow|like|share)\s+us\b"),
    re.compile(r"(?i)\b(click|tap)\s+here\b"),
]

_STOP_WORDS = frozenset([
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "it", "its",
    "this", "that", "these", "those", "he", "she", "they", "we", "you",
    "i", "me", "him", "her", "them", "us", "my", "your", "his", "our",
    "their", "not", "no", "nor", "so", "if", "then", "than", "too",
    "very", "just", "about", "also", "as", "into", "more", "some", "such",
    "what", "which", "who", "whom", "how", "when", "where", "why",
    "all", "each", "every", "both", "few", "many", "much", "own", "other",
    "any", "only", "same", "up", "out", "over", "after", "before",
    "between", "under", "again", "further", "once",
])


def _clean_text(text: str) -> str:
    """Clean and normalize text for summarization."""
    # Remove citation markers
    text = re.sub(r"\[\d+\]", "", text)
    # Normalize unicode quotes/dashes
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _is_boilerplate(sentence: str) -> bool:
    """Check if a sentence matches common boilerplate patterns."""
    return any(p.search(sentence) for p in _BOILERPLATE_PATTERNS)


def _split_sentences(text: str) -> list[str]:
    """
    Split text into sentences, handling abbreviations, decimals, and URLs.
    More robust than simple regex split.
    """
    # Protect abbreviations and decimals from splitting
    protected = text
    for abbr in _ABBREVIATIONS:
        # Match abbreviation followed by period and space
        pattern = re.compile(rf"\b({re.escape(abbr)})\.\s", re.IGNORECASE)
        protected = pattern.sub(rf"\1<PERIOD> ", protected)

    # Protect decimal numbers (e.g., 3.14)
    protected = re.sub(r"(\d)\.(\d)", r"\1<PERIOD>\2", protected)

    # Split on sentence-ending punctuation followed by space and capital letter or end
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z"\u201c])', protected)

    # Restore protected periods
    sentences = []
    for p in parts:
        restored = p.replace("<PERIOD>", ".").strip()
        if restored and len(restored.split()) >= 3:  # Skip fragments
            sentences.append(restored)

    return sentences


def _tokenize(text: str) -> list[str]:
    """Extract meaningful words, lowercased, without stop words."""
    words = re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text.lower())
    return [w for w in words if w not in _STOP_WORDS and len(w) > 1]


# ---------------------------------------------------------------------------
# TF-IDF computation
# ---------------------------------------------------------------------------

def _compute_tfidf(sentences: list[str]) -> list[dict[str, float]]:
    """Compute TF-IDF vectors for each sentence."""
    n = len(sentences)
    if n == 0:
        return []

    # Tokenize all sentences
    tokenized = [_tokenize(s) for s in sentences]

    # Document frequency
    df: Counter[str] = Counter()
    for tokens in tokenized:
        for term in set(tokens):
            df[term] += 1

    # IDF with smoothing
    idf = {term: math.log((n + 1) / (freq + 1)) + 1 for term, freq in df.items()}

    # TF-IDF per sentence
    tfidf_vectors = []
    for tokens in tokenized:
        if not tokens:
            tfidf_vectors.append({})
            continue
        tf = Counter(tokens)
        max_tf = max(tf.values())
        vec = {}
        for term, count in tf.items():
            # Augmented TF to prevent bias toward longer sentences
            augmented_tf = 0.5 + 0.5 * (count / max_tf)
            vec[term] = augmented_tf * idf.get(term, 1.0)
        tfidf_vectors.append(vec)

    return tfidf_vectors


def _cosine_similarity(v1: dict[str, float], v2: dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors."""
    if not v1 or not v2:
        return 0.0
    common = set(v1) & set(v2)
    if not common:
        return 0.0
    dot = sum(v1[k] * v2[k] for k in common)
    norm1 = math.sqrt(sum(x * x for x in v1.values()))
    norm2 = math.sqrt(sum(x * x for x in v2.values()))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def _sentence_centroid(tfidf_vectors: list[dict[str, float]]) -> dict[str, float]:
    """Compute centroid (average) TF-IDF vector across all sentences."""
    if not tfidf_vectors:
        return {}
    centroid: dict[str, float] = {}
    for vec in tfidf_vectors:
        for term, weight in vec.items():
            centroid[term] = centroid.get(term, 0.0) + weight
    n = len(tfidf_vectors)
    return {term: weight / n for term, weight in centroid.items()}


# ---------------------------------------------------------------------------
# MMR (Maximal Marginal Relevance) selection
# ---------------------------------------------------------------------------

def _mmr_select(
    sentences: list[str],
    tfidf_vectors: list[dict[str, float]],
    centroid: dict[str, float],
    scores: list[float],
    target_words: int,
    lambda_param: float = 0.6,
) -> list[tuple[int, str]]:
    """
    Select sentences using MMR to balance relevance and diversity.

    lambda_param controls trade-off: 1.0 = pure relevance, 0.0 = pure diversity.
    """
    selected: list[int] = []
    selected_vecs: list[dict[str, float]] = []
    remaining = set(range(len(sentences)))
    result_words = 0

    while remaining and result_words < target_words:
        best_idx = -1
        best_mmr = float("-inf")

        for idx in remaining:
            # Relevance to document centroid
            relevance = _cosine_similarity(tfidf_vectors[idx], centroid)
            # Boost by position/quality score
            relevance = relevance * 0.7 + scores[idx] * 0.3

            # Max similarity to already selected sentences (diversity penalty)
            max_sim = 0.0
            if selected_vecs:
                max_sim = max(
                    _cosine_similarity(tfidf_vectors[idx], sv)
                    for sv in selected_vecs
                )

            mmr = lambda_param * relevance - (1 - lambda_param) * max_sim
            if mmr > best_mmr:
                best_mmr = mmr
                best_idx = idx

        if best_idx < 0:
            break

        selected.append(best_idx)
        selected_vecs.append(tfidf_vectors[best_idx])
        remaining.discard(best_idx)
        result_words += len(sentences[best_idx].split())

    # Return in original document order for coherent reading
    selected.sort()
    return [(i, sentences[i]) for i in selected]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _target_word_count(num_words: int, min_w: int = 80, max_w: int = 300) -> int:
    target = max(min_w, int(num_words * 0.25))
    return min(target, max_w)


def summarize_extractive(
    text: str,
    min_words: int = 30,
    target_min: int = 80,
    target_max: int = 300,
) -> str:
    """
    Extract key sentences using TF-IDF scoring with MMR diversity.

    Returns a coherent summary built from the most informative sentences.
    """
    text = _clean_text(text)
    words = text.split()
    if len(words) < min_words:
        raise ValueError(f"Text too short. Minimum {min_words} words.")

    sentences = _split_sentences(text)
    if not sentences:
        return text[:500]

    # Filter out boilerplate sentences
    clean_sentences = []
    clean_indices = []
    for i, s in enumerate(sentences):
        if not _is_boilerplate(s):
            clean_sentences.append(s)
            clean_indices.append(i)

    if not clean_sentences:
        clean_sentences = sentences
        clean_indices = list(range(len(sentences)))

    target_words = _target_word_count(len(words), target_min, target_max)
    n = len(clean_sentences)

    # Compute TF-IDF vectors
    tfidf_vectors = _compute_tfidf(clean_sentences)
    centroid = _sentence_centroid(tfidf_vectors)

    # Compute per-sentence scores (TF-IDF relevance + position bonus)
    scores: list[float] = []
    for i, (sent, vec) in enumerate(zip(clean_sentences, tfidf_vectors)):
        # TF-IDF relevance to document centroid
        tfidf_score = _cosine_similarity(vec, centroid)

        # Position scoring: first 15% and last 10% of sentences get a boost
        original_pos = clean_indices[i] / max(len(sentences) - 1, 1)
        if original_pos < 0.15:
            pos_bonus = 0.25
        elif original_pos > 0.9:
            pos_bonus = 0.15
        else:
            pos_bonus = 0.0

        # Length normalization: prefer sentences of 10-30 words
        wc = len(sent.split())
        if 10 <= wc <= 30:
            length_bonus = 0.1
        elif wc < 5:
            length_bonus = -0.3
        else:
            length_bonus = 0.0

        # Bonus for sentences with numbers (likely contain data/evidence)
        has_numbers = bool(re.search(r"\d+(?:\.\d+)?%?", sent))
        number_bonus = 0.08 if has_numbers else 0.0

        # Bonus for sentences with named entities (capitalized sequences)
        has_entities = bool(re.search(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", sent))
        entity_bonus = 0.05 if has_entities else 0.0

        final_score = tfidf_score + pos_bonus + length_bonus + number_bonus + entity_bonus
        scores.append(final_score)

    # MMR selection for diversity
    selected = _mmr_select(
        clean_sentences, tfidf_vectors, centroid, scores, target_words
    )

    if not selected:
        return text[:500]

    summary = " ".join(s for _, s in selected)
    return summary.strip()
