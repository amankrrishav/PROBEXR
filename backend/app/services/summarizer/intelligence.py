"""
Summarizer Intelligence: NLP utilities for text cleaning, content-type detection,
readability scoring, quotes, entities, and sentiment analysis.
"""
import re
from typing import Any

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
    re.compile(r"(?i)^\s*(related\s+articles?|you\s+may\s+also\s+like|recommended)\s*[:\.]?.*$", re.MULTILINE),
    re.compile(r"(?i)^\s*(table\s+of\s+contents?)\s*$", re.MULTILINE),
    re.compile(r"(?i)^\s*(leave\s+a\s+comment|comments?\s+section).*$", re.MULTILINE),
    re.compile(r"(?i)^\s*(last\s+updated|published|modified)\s*:?\s*\d.*$", re.MULTILINE),
    re.compile(r"(?i)^\s*tags?\s*:.*$", re.MULTILINE),
    re.compile(r"(?i)\b(accept\s+(all\s+)?cookies?)\b.*$", re.MULTILINE),
    re.compile(r"(?i)\b(we\s+use\s+cookies?)\b.*$", re.MULTILINE),
]

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

def clean_text(text: str) -> str:
    """Aggressively clean text: remove boilerplate, normalize unicode, collapse whitespace."""
    # Remove citation markers [1], [2], etc.
    text = re.sub(r"\[\d+\]", "", text)

    # Normalize unicode
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", " — ")
    text = text.replace("\u00a0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("\u2026", "...")
    text = text.replace("\u200e", "")
    text = text.replace("\u200f", "")
    text = text.replace("\ufeff", "")

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

def detect_content_type(text: str) -> str:
    """Classify content as: academic, news, technical, opinion, or general."""
    academic = len(_ACADEMIC_SIGNALS.findall(text))
    news = len(_NEWS_SIGNALS.findall(text))
    tech = len(_TECH_SIGNALS.findall(text))
    opinion = len(_OPINION_SIGNALS.findall(text))

    scores = {
        "academic": academic * 2,
        "news": news,
        "technical": tech,
        "opinion": opinion,
    }

    best = max(list(scores.keys()), key=lambda k: scores[k])
    if scores[best] < 3:
        return "general"
    return best

def readability_score(text: str) -> tuple[float, str]:
    """Compute Flesch Reading Ease score and human label."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s for s in sentences if s.strip()]
    words = re.findall(r"[a-zA-Z']+", text)

    if not sentences or not words:
        return 50.0, "Average"

    total_sentences = len(sentences)
    total_words = len(words)
    syllables = sum(max(1, len(re.findall(r"[aeiouy]+", w.lower().rstrip("e")))) for w in words)

    asl = total_words / total_sentences
    asw = syllables / total_words
    score = 206.835 - (1.015 * asl) - (84.6 * asw)
    score = round(max(0, min(100, int(score))), 1)

    if score >= 80: label = "Very Easy"
    elif score >= 65: label = "Easy"
    elif score >= 50: label = "Average"
    elif score >= 35: label = "Moderate"
    elif score >= 20: label = "Difficult"
    else: label = "Very Difficult"

    return score, label

def extract_notable_quotes(text: str, max_quotes: int = 3) -> list[str]:
    """Extract notable substantive direct quotes from source."""
    patterns = [re.compile(r'["\u201c]([^"\u201d]{20,200})["\u201d]')]
    quotes = []
    for pattern in patterns:
        for match in pattern.finditer(text):
            q = match.group(1).strip()
            # Simple heuristic filters
            if len(q.split()) >= 5 and not (q.endswith(":") or q.startswith("http")):
                quotes.append(q)
    
    unique: list[str] = []
    seen = set()
    for quote in sorted(quotes, key=len, reverse=True):
        quote_str = str(quote)
        key = quote_str.lower()[:50]
        if key not in seen:
            seen.add(key)
            unique.append(quote_str)
    return unique[:max_quotes]

def extract_entities_fallback(text: str) -> dict[str, list[str]]:
    """Regex-based fallback for entity extraction if LLM fails or for augmentation."""
    # Simple Capitalized Word sequences (crude but effective fallback)
    people = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", text)
    orgs = re.findall(r"\b[A-Z][A-Z\d]+\b", text) # Acronyms
    
    return {
        "people": list(set(people))[:5],
        "orgs": list(set(orgs))[:5],
        "concepts": []
    }

def compute_complexity_score(text: str) -> int:
    """Combines readability, vocabulary variety, and sentence length into a 1-10 score."""
    words = re.findall(r"\w+", text.lower())
    if not words: return 5
    
    unique_ratio = len(set(words)) / len(words)
    avg_word_len = sum(len(w) for w in words) / len(words)
    
    # Heuristic score
    score = (avg_word_len * 2) + (unique_ratio * 5)
    return max(1, min(10, round(score)))

def compute_metadata(original_text: str, summary_text: str, llm_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Assembles all rich intelligence metadata."""
    orig_words = original_text.split()
    summ_words = summary_text.split()
    orig_wc = len(orig_words)
    summ_wc = len(summ_words)
    
    # Base stats
    meta = {
        "original_word_count": orig_wc,
        "summary_word_count": summ_wc,
        "compression_ratio": round(float(1 - summ_wc / max(orig_wc, 1)) * 100, 1),
        "reading_time_seconds": max(1, round(summ_wc / 200 * 60)),
        "content_type": detect_content_type(original_text),
        "complexity_score": compute_complexity_score(original_text),
    }

    # NLP stats
    r_score, r_label = readability_score(summary_text)
    meta.update({
        "readability_score": r_score,
        "readability_label": r_label,
        "notable_quotes": extract_notable_quotes(original_text),
    })

    # Integrate/Augment LLM-provided metadata
    llm = llm_metadata or {}
    
    fallback_entities = extract_entities_fallback(original_text)
    llm_entities = llm.get("entities", {})
    
    # Merge entities (prefer LLM, but use fallback if LLM is sparse)
    meta["entities"] = {
        "people": list(set(llm_entities.get("people", []) + fallback_entities["people"]))[:8],
        "orgs": list(set(llm_entities.get("orgs", []) + fallback_entities["orgs"]))[:8],
        "concepts": llm_entities.get("concepts", [])[:8],
    }
    
    meta.update({
        "tldr": llm.get("tldr", ""),
        "sentiment": llm.get("sentiment", "Neutral"),
        "tone": llm.get("professional_tone", "Professional"),
    })

    return meta
