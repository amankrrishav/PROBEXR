"""
Production-grade extractive summarizer — no API key, no cost.

Uses TextRank (graph-based) + TF-IDF hybrid scoring with:
  - PageRank-style sentence importance ranking
  - Topic coverage optimization (ensures all major themes are represented)
  - Cue phrase detection (conclusion markers, importance signals)
  - MMR diversity selection (eliminates redundancy)
  - Smart takeaway extraction (highest info-density sentences)

Quality comparable to early-2020s NLP research systems.
"""
import math
import re
from collections import Counter
from typing import Any


# ---------------------------------------------------------------------------
# Text cleaning & sentence segmentation
# ---------------------------------------------------------------------------

_ABBREVIATIONS = frozenset([
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc",
    "inc", "ltd", "co", "corp", "dept", "univ", "govt", "approx",
    "fig", "vol", "no", "jan", "feb", "mar", "apr", "jun", "jul",
    "aug", "sep", "oct", "nov", "dec", "al", "e.g", "i.e",
])

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
    "between", "under", "again", "further", "once", "there", "here",
    "most", "such", "through", "during", "because", "while", "although",
    "since", "until", "whether", "though", "even", "still", "already",
    "yet", "now", "well", "back", "get", "got", "make", "made",
    "said", "like", "new", "one", "two", "first", "last", "way",
])

# Cue phrases that signal important sentences
_CUE_PHRASES_STRONG = [
    re.compile(r"(?i)\b(in\s+conclusion|to\s+summarize|in\s+summary|overall|ultimately)\b"),
    re.compile(r"(?i)\b(most\s+important(?:ly)?|key\s+finding|significant(?:ly)?|critical(?:ly)?)\b"),
    re.compile(r"(?i)\b(results?\s+show|data\s+(?:shows?|suggests?|indicates?)|evidence\s+suggests?)\b"),
    re.compile(r"(?i)\b(according\s+to|research\s+(?:shows?|suggests?|found|indicates?))\b"),
    re.compile(r"(?i)\b(the\s+main|the\s+primary|the\s+key|the\s+central)\b"),
]

_CUE_PHRASES_MODERATE = [
    re.compile(r"(?i)\b(however|nevertheless|in\s+contrast|on\s+the\s+other\s+hand)\b"),
    re.compile(r"(?i)\b(therefore|consequently|as\s+a\s+result|thus|hence)\b"),
    re.compile(r"(?i)\b(for\s+example|for\s+instance|specifically|in\s+particular)\b"),
    re.compile(r"(?i)\b(notably|importantly|remarkably|interestingly)\b"),
    re.compile(r"(?i)\b(despite|although|while|whereas)\b"),
]


def _clean_text(text: str) -> str:
    """Clean and normalize text for summarization."""
    text = re.sub(r"\[\d+\]", "", text)
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", " — ")
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _is_boilerplate(sentence: str) -> bool:
    return any(p.search(sentence) for p in _BOILERPLATE_PATTERNS)


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, handling abbreviations and decimals."""
    protected = text
    for abbr in _ABBREVIATIONS:
        pattern = re.compile(rf"\b({re.escape(abbr)})\.\s", re.IGNORECASE)
        protected = pattern.sub(rf"\1<PERIOD> ", protected)

    protected = re.sub(r"(\d)\.(\d)", r"\1<PERIOD>\2", protected)

    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z"\u201c])', protected)

    sentences = []
    for p in parts:
        restored = p.replace("<PERIOD>", ".").strip()
        if restored and len(restored.split()) >= 3:
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

    tokenized = [_tokenize(s) for s in sentences]

    df: Counter = Counter()
    for tokens in tokenized:
        for term in set(tokens):
            df[term] += 1

    idf = {term: math.log((n + 1) / (freq + 1)) + 1 for term, freq in df.items()}

    tfidf_vectors: list[dict[str, float]] = []
    for tokens in tokenized:
        if not tokens:
            tfidf_vectors.append({})
            continue
        tf = Counter(tokens)
        max_tf = max(tf.values())
        vec: dict[str, float] = {}
        for term, count in tf.items():
            augmented_tf = 0.5 + 0.5 * (count / max_tf)
            vec[term] = augmented_tf * idf.get(term, 1.0)
        tfidf_vectors.append(vec)

    return tfidf_vectors


def _cosine_similarity(v1: dict[str, float], v2: dict[str, float]) -> float:
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
    if not tfidf_vectors:
        return {}
    centroid: dict[str, float] = {}
    for vec in tfidf_vectors:
        for term, weight in vec.items():
            centroid[term] = centroid.get(term, 0.0) + weight
    n = len(tfidf_vectors)
    return {term: weight / n for term, weight in centroid.items()}


# ---------------------------------------------------------------------------
# TextRank — graph-based sentence ranking (PageRank on similarity graph)
# ---------------------------------------------------------------------------

def _textrank_scores(
    sentences: list[str],
    tfidf_vectors: list[dict[str, float]],
    damping: float = 0.85,
    iterations: int = 30,
    convergence: float = 0.0001,
) -> list[float]:
    """
    Compute TextRank scores for sentences using PageRank on a similarity graph.

    Each sentence is a node. Edge weights are cosine similarities between
    TF-IDF vectors. Sentences connected to many important sentences rank higher.
    """
    n = len(sentences)
    if n == 0:
        return []
    if n == 1:
        return [1.0]

    # Build similarity matrix (only upper triangle needed, symmetric)
    sim_matrix: list[list[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            sim = _cosine_similarity(tfidf_vectors[i], tfidf_vectors[j])
            if sim > 0.05:  # threshold to avoid noise edges
                sim_matrix[i][j] = sim
                sim_matrix[j][i] = sim

    # Compute out-degree (sum of edge weights) for normalization
    out_degree = [sum(row) for row in sim_matrix]

    # Initialize scores uniformly
    scores = [1.0 / n] * n

    # Power iteration (PageRank)
    for _ in range(iterations):
        new_scores = [0.0] * n
        max_delta = 0.0

        for i in range(n):
            rank_sum = 0.0
            for j in range(n):
                if j != i and out_degree[j] > 0:
                    rank_sum += (sim_matrix[j][i] / out_degree[j]) * scores[j]

            new_scores[i] = (1 - damping) / n + damping * rank_sum
            max_delta = max(max_delta, abs(new_scores[i] - scores[i]))

        scores = new_scores
        if max_delta < convergence:
            break

    # Normalize to [0, 1]
    max_score = max(scores) if scores else 1.0
    if max_score > 0:
        scores = [s / max_score for s in scores]

    return scores


# ---------------------------------------------------------------------------
# Topic clustering — ensure summary covers all major themes
# ---------------------------------------------------------------------------

def _cluster_sentences(
    tfidf_vectors: list[dict[str, float]],
    n_clusters: int = 4,
) -> list[int]:
    """
    Simple greedy clustering by TF-IDF similarity.
    Assigns each sentence to the nearest cluster centroid.
    Returns list of cluster IDs.
    """
    n = len(tfidf_vectors)
    if n <= n_clusters:
        return list(range(n))

    # Initialize centroids as the first n_clusters sentences that are most different
    centroid_indices = [0]
    for _ in range(1, n_clusters):
        max_min_dist = -1.0
        best_idx = -1
        for i in range(n):
            if i in centroid_indices:
                continue
            min_dist = min(
                _cosine_similarity(tfidf_vectors[i], tfidf_vectors[c])
                for c in centroid_indices
            )
            # We want the sentence most DIFFERENT from existing centroids
            # so we maximize the minimum distance (furthest from all centroids)
            if (1.0 - min_dist) > max_min_dist:
                max_min_dist = 1.0 - min_dist
                best_idx = i
        if best_idx >= 0:
            centroid_indices.append(best_idx)

    # Assign each sentence to nearest centroid
    assignments = [0] * n
    for i in range(n):
        best_cluster = 0
        best_sim = -1.0
        for ci, c_idx in enumerate(centroid_indices):
            sim = _cosine_similarity(tfidf_vectors[i], tfidf_vectors[c_idx])
            if sim > best_sim:
                best_sim = sim
                best_cluster = ci
        assignments[i] = best_cluster

    return assignments


# ---------------------------------------------------------------------------
# Cue phrase and content signal scoring
# ---------------------------------------------------------------------------

def _cue_phrase_score(sentence: str) -> float:
    """Score based on presence of discourse markers that signal importance."""
    score = 0.0
    for pattern in _CUE_PHRASES_STRONG:
        if pattern.search(sentence):
            score += 0.15
            break  # one strong cue is enough
    for pattern in _CUE_PHRASES_MODERATE:
        if pattern.search(sentence):
            score += 0.08
            break
    return min(score, 0.20)  # cap


def _content_signal_score(sentence: str) -> float:
    """Score based on information density signals."""
    score = 0.0

    # Numbers with context (percentages, dollar amounts, specific quantities)
    if re.search(r"\d+(?:\.\d+)?\s*(?:percent|%)", sentence, re.IGNORECASE):
        score += 0.12
    elif re.search(r"\$\d+|\d+(?:\.\d+)?\s*(?:billion|million|trillion|thousand)", sentence, re.IGNORECASE):
        score += 0.12
    elif re.search(r"\d+(?:\.\d+)?", sentence):
        score += 0.06

    # Quotation marks (likely a direct quote — high info value)
    if re.search(r'["\u201c].*?["\u201d]', sentence):
        score += 0.08

    # Named entities (consecutive capitalized words)
    named_entities = re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", sentence)
    if named_entities:
        score += min(0.08, len(named_entities) * 0.04)

    # Superlatives and comparatives (signal key claims)
    if re.search(r"(?i)\b(most|largest|smallest|highest|lowest|best|worst|first|biggest)\b", sentence):
        score += 0.05

    return min(score, 0.25)  # cap


def _position_score(idx: int, total_sentences: int, original_idx: int, original_total: int) -> float:
    """
    Score based on sentence position in the document.
    Lead sentences and conclusion sentences carry more weight.
    """
    if original_total <= 1:
        return 0.15

    relative_pos = original_idx / (original_total - 1)

    # Lead bias: first 10% of sentences (introduction, thesis)
    if relative_pos < 0.10:
        return 0.25

    # Conclusion bias: last 8% of sentences
    if relative_pos > 0.92:
        return 0.18

    # Paragraph-lead heuristic: give slight boost to early sentences
    if relative_pos < 0.20:
        return 0.12

    # Mid-document slight penalty (filler zone)
    if 0.4 < relative_pos < 0.6:
        return 0.02

    return 0.06


# ---------------------------------------------------------------------------
# Hybrid scoring — combines all signals
# ---------------------------------------------------------------------------

def _compute_hybrid_scores(
    sentences: list[str],
    original_indices: list[int],
    original_total: int,
    tfidf_vectors: list[dict[str, float]],
    centroid: dict[str, float],
    textrank_scores: list[float],
) -> list[float]:
    """
    Combine TextRank (40%) + TF-IDF centroid (25%) + Position (15%) +
    Cue phrases (10%) + Content signals (10%) into final scores.
    """
    n = len(sentences)
    scores: list[float] = []

    for i in range(n):
        # 1. TextRank (graph-based importance) — 40%
        tr_score = textrank_scores[i] * 0.40

        # 2. TF-IDF centroid relevance — 25%
        tfidf_score = _cosine_similarity(tfidf_vectors[i], centroid) * 0.25

        # 3. Position — 15%
        pos_score = _position_score(i, n, original_indices[i], original_total) * 0.15 / 0.25

        # 4. Cue phrases — 10%
        cue_score = _cue_phrase_score(sentences[i]) * 0.10 / 0.20

        # 5. Content signals — 10%
        content_score = _content_signal_score(sentences[i]) * 0.10 / 0.25

        # Length penalty: reject very short sentences
        wc = len(sentences[i].split())
        length_penalty = 0.0
        if wc < 5:
            length_penalty = -0.3
        elif wc < 8:
            length_penalty = -0.1

        final = tr_score + tfidf_score + pos_score + cue_score + content_score + length_penalty
        scores.append(max(0.0, final))

    return scores


# ---------------------------------------------------------------------------
# Selection with topic coverage + MMR diversity
# ---------------------------------------------------------------------------

def _select_sentences_with_coverage(
    sentences: list[str],
    scores: list[float],
    tfidf_vectors: list[dict[str, float]],
    cluster_assignments: list[int],
    target_words: int,
    lambda_param: float = 0.6,
) -> list[int]:
    """
    Select sentences balancing:
    1. Score (hybrid importance)
    2. Topic coverage (ensure all clusters represented)
    3. Diversity (MMR — avoid redundancy)
    """
    n = len(sentences)
    selected: list[int] = []
    selected_vecs: list[dict[str, float]] = []
    remaining = set(range(n))
    result_words = 0

    # Phase 1: Ensure topic coverage — pick top sentence from each cluster
    n_clusters = max(cluster_assignments) + 1 if cluster_assignments else 0
    covered_clusters: set[int] = set()

    # Sort clusters by their best sentence score (cover important topics first)
    cluster_best: list[tuple[float, int, int]] = []  # (score, cluster_id, sentence_idx)
    for cluster_id in range(n_clusters):
        cluster_sentences = [i for i in range(n) if cluster_assignments[i] == cluster_id]
        if cluster_sentences:
            best_in_cluster = max(cluster_sentences, key=lambda x: scores[x])
            cluster_best.append((scores[best_in_cluster], cluster_id, best_in_cluster))
    cluster_best.sort(reverse=True)

    for _, cluster_id, sent_idx in cluster_best:
        if result_words >= target_words:
            break
        if sent_idx in remaining and cluster_id not in covered_clusters:
            selected.append(sent_idx)
            selected_vecs.append(tfidf_vectors[sent_idx])
            remaining.discard(sent_idx)
            covered_clusters.add(cluster_id)
            result_words += len(sentences[sent_idx].split())

    # Phase 2: Fill remaining budget with MMR selection
    while remaining and result_words < target_words:
        best_idx = -1
        best_mmr = float("-inf")

        for idx in remaining:
            # Relevance (hybrid score)
            relevance = scores[idx]

            # Diversity penalty (max similarity to already selected)
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
    return selected


# ---------------------------------------------------------------------------
# Smart takeaway extraction
# ---------------------------------------------------------------------------

def extract_takeaways(
    sentences: list[str],
    scores: list[float],
    tfidf_vectors: list[dict[str, float]],
    count: int = 5,
) -> list[str]:
    """
    Extract the most informative standalone sentences as key takeaways.

    Prioritizes sentences with:
    1. High content signal scores (numbers, specifics, named entities)
    2. High overall importance (hybrid score)
    3. Self-containedness (can be understood without context)
    4. Diversity (different topics)
    """
    n = len(sentences)
    if n == 0:
        return []

    # Score each sentence for takeaway quality
    takeaway_scores: list[tuple[float, int]] = []
    for i in range(n):
        # Content density (numbers, entities, quotes) is the primary signal
        content_score = _content_signal_score(sentences[i])

        # Hybrid importance as secondary signal
        hybrid_score = scores[i] if i < len(scores) else 0.0

        # Self-containedness: penalize sentences starting with pronouns or
        # references (they require context to understand)
        self_contained_penalty = 0.0
        first_word = sentences[i].split()[0].lower() if sentences[i] else ""
        if first_word in ("it", "this", "that", "these", "those", "they", "he", "she", "its", "their", "his", "her"):
            self_contained_penalty = -0.15
        elif first_word in ("however", "but", "also", "moreover", "furthermore", "additionally"):
            self_contained_penalty = -0.08

        # Prefer sentences of 10-30 words (readable standalone)
        wc = len(sentences[i].split())
        length_bonus = 0.0
        if 12 <= wc <= 35:
            length_bonus = 0.05
        elif wc < 8 or wc > 50:
            length_bonus = -0.1

        # Cue phrases boost
        cue_bonus = _cue_phrase_score(sentences[i]) * 0.5

        total = (content_score * 0.35 + hybrid_score * 0.35 +
                 cue_bonus * 0.15 + length_bonus + self_contained_penalty)
        takeaway_scores.append((total, i))

    # Sort by score, then select with diversity
    takeaway_scores.sort(reverse=True)

    selected: list[int] = []
    selected_vecs: list[dict[str, float]] = []

    for score, idx in takeaway_scores:
        if len(selected) >= count:
            break

        # Diversity check: reject if too similar to already picked takeaway
        if selected_vecs and idx < len(tfidf_vectors):
            max_sim = max(
                _cosine_similarity(tfidf_vectors[idx], sv)
                for sv in selected_vecs
            )
            if max_sim > 0.6:  # 60% similarity threshold
                continue

        selected.append(idx)
        if idx < len(tfidf_vectors):
            selected_vecs.append(tfidf_vectors[idx])

    # Return in document order
    selected.sort()
    return [sentences[i] for i in selected]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _target_word_count(num_words: int, min_w: int = 80, max_w: int = 300, ratio: float = 0.25) -> int:
    target = max(min_w, int(num_words * ratio))
    return min(target, max_w)


def summarize_extractive(
    text: str,
    min_words: int = 30,
    target_min: int = 80,
    target_max: int = 300,
    word_ratio: float = 0.25,
    takeaway_count: int = 5,
) -> dict[str, Any]:
    """
    Extract key sentences using TextRank + hybrid scoring with topic coverage.

    Returns a dict with:
      - 'summary': str — coherent extractive summary
      - 'key_takeaways': list[str] — highest info-density standalone sentences
    """
    text = _clean_text(text)
    words = text.split()
    if len(words) < min_words:
        raise ValueError(f"Text too short. Minimum {min_words} words.")

    sentences = _split_sentences(text)
    if not sentences:
        return {"summary": text[:500], "key_takeaways": []}

    # Filter boilerplate
    clean_sentences: list[str] = []
    clean_indices: list[int] = []
    for i, s in enumerate(sentences):
        if not _is_boilerplate(s):
            clean_sentences.append(s)
            clean_indices.append(i)

    if not clean_sentences:
        clean_sentences = sentences
        clean_indices = list(range(len(sentences)))

    target_words = _target_word_count(len(words), target_min, target_max, ratio=word_ratio)
    n = len(clean_sentences)
    total_original = len(sentences)

    # 1. Compute TF-IDF vectors
    tfidf_vectors = _compute_tfidf(clean_sentences)
    centroid = _sentence_centroid(tfidf_vectors)

    # 2. Compute TextRank scores
    tr_scores = _textrank_scores(clean_sentences, tfidf_vectors)

    # 3. Compute hybrid scores
    hybrid_scores = _compute_hybrid_scores(
        clean_sentences, clean_indices, total_original,
        tfidf_vectors, centroid, tr_scores,
    )

    # 4. Cluster sentences for topic coverage
    n_clusters = min(max(3, n // 5), 6)  # 3-6 clusters depending on article length
    cluster_assignments = _cluster_sentences(tfidf_vectors, n_clusters=n_clusters)

    # 5. Select sentences with coverage + diversity
    selected_indices = _select_sentences_with_coverage(
        clean_sentences, hybrid_scores, tfidf_vectors,
        cluster_assignments, target_words,
    )

    if not selected_indices:
        return {"summary": text[:500], "key_takeaways": []}

    summary = " ".join(clean_sentences[i] for i in selected_indices)

    # 6. Extract smart takeaways (different from summary selection!)
    takeaways = extract_takeaways(
        clean_sentences, hybrid_scores, tfidf_vectors, count=takeaway_count,
    )

    return {
        "summary": summary.strip(),
        "key_takeaways": takeaways,
    }
