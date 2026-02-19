import { syllable } from "syllable";

function countSentences(text) {
  const matches = text.match(/[^.!?]+[.!?]+/g);
  return matches ? matches.length : 1;
}

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

function getTopComplexWords(wordList, count = 5) {
  const stopWords = new Set([
    "the","and","that","this","with","from","they","have",
    "been","were","their","about","which","when","there",
    "would","could","should"
  ]);

  return [...new Set(
    wordList
      .map(w => w.replace(/[^a-zA-Z]/g, "").toLowerCase())
      .filter(w => w.length > 3 && !stopWords.has(w))
      .sort((a, b) => syllable(b) - syllable(a))
  )].slice(0, count);
}

export function getDifficulty(text) {
  const wordList = text.trim().split(/\s+/);
  const words = wordList.length;
  const sentences = countSentences(text);
  const syllables = wordList.reduce((acc, w) => acc + syllable(w), 0);

  const fk =
    0.39 * (words / sentences) +
    11.8 * (syllables / words) -
    15.59;

  const score = fkToScore(fk);
  const { label, color } = getLabel(score);
  const topWords = getTopComplexWords(wordList);

  const avgWordLen = (
    wordList.reduce(
      (acc, w) => acc + w.replace(/[^a-zA-Z]/g, "").length,
      0
    ) / words
  ).toFixed(1);

  const avgSentenceLen = (words / sentences).toFixed(1);

  return {
    score,
    label,
    color,
    fk: fk.toFixed(1),
    avgWordLen,
    avgSentenceLen,
    topWords
  };
}