import { syllable } from "syllable";

// ==============================
// 1️⃣ Sentence Counting
// ==============================

function countSentences(text, words) {
  const matches = text.match(/[^.!?]+[.!?]+/g);
  if (matches && matches.length > 0) return matches.length;

  return Math.max(1, Math.round(words / 20));
}

// ==============================
// 2️⃣ FK Score Mapping
// ==============================

function fkToScore(fk) {
  const clamped = Math.max(0, Math.min(18, fk));
  return Math.round((clamped / 18) * 9) + 1;
}

function getLabel(score) {
  if (score <= 3) return { label: "Easy", color: "#22c55e" };
  if (score <= 5) return { label: "Moderate", color: "#84cc16" };
  if (score <= 7) return { label: "Dense", color: "#f59e0b" };
  return { label: "Academic", color: "#ef4444" };
}

// ==============================
// 3️⃣ Complex Word Extraction
// ==============================

function getTopComplexWords(wordList, count = 5) {
  const stopWords = new Set([
    "the","and","that","this","with","from","they","have",
    "been","were","their","about","which","when","there",
    "would","could","should"
  ]);

  const cleaned = wordList
    .map(w => w.replace(/[^a-zA-Z]/g, "").toLowerCase())
    .filter(w => w.length > 3 && !stopWords.has(w));

  const unique = [...new Set(cleaned)];

  return unique
    .sort((a, b) => syllable(b) - syllable(a))
    .slice(0, count);
}

// ==============================
// 4️⃣ PUBLIC FEATURE ENGINE
// ==============================

export function getDifficulty(text) {
  const wordList = text.trim().split(/\s+/).filter(Boolean);
  const words = wordList.length;

  if (words === 0) {
    return {
      score: 1,
      label: "Easy",
      color: "#22c55e",
      features: {},
      topWords: []
    };
  }

  const sentences = countSentences(text, words);

  const syllables = wordList.reduce(
    (acc, w) => acc + syllable(w),
    0
  );

  const avgSentenceLength = words / sentences;
  const avgSyllablesPerWord = syllables / words;

  const fk =
    0.39 * avgSentenceLength +
    11.8 * avgSyllablesPerWord -
    15.59;

  const score = fkToScore(fk);
  const { label, color } = getLabel(score);
  const topWords = getTopComplexWords(wordList);

  // ==========================
  // 🔬 ML Feature Vector
  // ==========================

  const features = {
    wordCount: words,
    sentenceCount: sentences,
    avgSentenceLength,
    avgSyllablesPerWord,
    fkRaw: fk,
    lexicalDensity: topWords.length / words
  };

  return {
    score,
    label,
    color,
    fk: fk.toFixed(1),
    avgWordLen: (
      wordList.reduce(
        (acc, w) => acc + w.replace(/[^a-zA-Z]/g, "").length,
        0
      ) / words
    ).toFixed(1),
    avgSentenceLen: avgSentenceLength.toFixed(1),
    topWords,
    features
  };
}