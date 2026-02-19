export function generateSummary(text) {
  if (!text) return "Summary unavailable.";

  const sentences = text.match(/[^.!?]+[.!?]+/g);
  if (!sentences || sentences.length === 0) {
    return text.slice(0, 140) + "...";
  }

  // --- CLEAN & TOKENIZE ---
  const words = text
    .toLowerCase()
    .replace(/[^a-zA-Z\s]/g, "")
    .split(/\s+/)
    .filter(Boolean);

  const stopWords = new Set([
    "the","and","that","this","with","from","they","have",
    "been","were","their","about","which","when","there",
    "would","could","should","into","while","where",
    "also","very","such","many","some","most","more"
  ]);

  // --- BUILD FREQUENCY MAP ---
  const freq = {};
  words.forEach(word => {
    if (word.length > 3 && !stopWords.has(word)) {
      freq[word] = (freq[word] || 0) + 1;
    }
  });

  const maxFreq = Math.max(...Object.values(freq), 1);

  let bestSentence = sentences[0].trim();
  let bestScore = 0;

  const pivotWords = [
    "however","but","therefore","thus",
    "as a result","consequently","instead"
  ];

  const conclusionWords = [
    "ultimately","overall","in conclusion",
    "in summary","in the end"
  ];

  sentences.forEach((sentence, index) => {
    const clean = sentence.trim();
    const lower = clean.toLowerCase();

    const sentenceWords = lower
      .replace(/[^a-zA-Z\s]/g, "")
      .split(/\s+/)
      .filter(Boolean);

    if (sentenceWords.length < 6) return;

    let score = 0;

    // 1️⃣ Normalized TF score
    sentenceWords.forEach(word => {
      if (freq[word]) {
        score += freq[word] / maxFreq;
      }
    });

    score = score / sentenceWords.length;

    // 2️⃣ Smooth positional decay (less aggressive)
    score *= 1 / (1 + index * 0.15);

    // 3️⃣ Definition boost (for encyclopedia style)
    if (/is|are|refers to|defined as/.test(lower) && index <= 2) {
      score *= 1.4;
    }

    // 4️⃣ Pivot boost
    if (pivotWords.some(word => lower.includes(word))) {
      score *= 1.25;
    }

    // 5️⃣ Conclusion boost
    if (conclusionWords.some(word => lower.includes(word))) {
      score *= 1.4;
    }

    // 6️⃣ Abstract concept bonus
    const abstractMatches = lower.match(/(tion|ment|ity|ness|ism)\b/gi);
    if (abstractMatches) {
      score += abstractMatches.length * 0.3;
    }

    // 7️⃣ Length penalty (too long = diluted)
    if (sentenceWords.length > 35) {
      score *= 0.85;
    }

    // 8️⃣ List-style penalty
    if (/^(first|second|third|finally)/i.test(clean)) {
      score *= 0.6;
    }

    if (score > bestScore) {
      bestScore = score;
      bestSentence = clean;
    }
  });

  return bestSentence;
}