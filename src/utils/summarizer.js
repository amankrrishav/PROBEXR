// =============================
// 1️⃣ CORE SCORING ENGINE
// =============================

function generateCoreSummary(text) {
  if (!text) return "Summary unavailable.";

  const sentences = text.match(/[^.!?]+[.!?]+/g);
  if (!sentences || sentences.length === 0) {
    return text.slice(0, 140) + "...";
  }

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

    // 1️⃣ Normalized term frequency
    sentenceWords.forEach(word => {
      if (freq[word]) {
        score += freq[word] / maxFreq;
      }
    });

    score = score / sentenceWords.length;

    // 2️⃣ Smooth positional decay
    score *= 1 / (1 + index * 0.15);

    // 3️⃣ Definition boost
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

    // 6️⃣ Abstract concept density bonus
    const abstractMatches = lower.match(/(tion|ment|ity|ness|ism)\b/gi);
    if (abstractMatches) {
      score += abstractMatches.length * 0.3;
    }

    // 7️⃣ Length penalty
    if (sentenceWords.length > 35) {
      score *= 0.85;
    }

    // 8️⃣ List penalty
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


// =============================
// 2️⃣ TEXT PROFILE ENGINE
// =============================

function computeTextProfile(text, difficultyScore) {
  const lower = text.toLowerCase();
  const words = lower.split(/\s+/);
  const totalWords = words.length;

  const abstractMatches = lower.match(/(tion|ment|ity|ness|ism)\b/gi) || [];
  const abstractDensity = abstractMatches.length / totalWords;

  const technicalSignals = [
    "model","data","analysis","theory",
    "empirical","quantitative","probability",
    "optimization","framework","algorithm"
  ];

  const narrativeSignals = [
    "he","she","they","once","when",
    "after","before","story","journey"
  ];

  let techScore = 0;
  let narrativeScore = 0;

  technicalSignals.forEach(w => {
    if (lower.includes(w)) techScore++;
  });

  narrativeSignals.forEach(w => {
    if (lower.includes(w)) narrativeScore++;
  });

  if (difficultyScore <= 4) return "simple";
  if (techScore > 2 || abstractDensity > 0.08) return "technical";
  if (narrativeScore > techScore) return "story";
  return "analytical";
}


// =============================
// 3️⃣ STYLE TRANSFORMERS
// =============================

function simplify(sentence) {
  return sentence
    .replace(/demonstrates|indicates/gi, "shows")
    .replace(/therefore|thus/gi, "so")
    .replace(/approximately/gi, "about")
    .replace(/ultimately/gi, "in the end");
}

function compress(sentence) {
  return sentence
    .replace(/\bshows\b/gi, "empirically demonstrates")
    .replace(/\bidea\b/gi, "conceptual framework");
}

function preserveNarrativeTone(sentence) {
  return sentence.replace(/^Ultimately,/i, "In the end,");
}


// =============================
// 4️⃣ PUBLIC EXPORT
// =============================

export function generateAdaptiveSummary(text, difficultyScore) {
  const profile = computeTextProfile(text, difficultyScore);
  const baseSummary = generateCoreSummary(text);

  switch(profile) {
    case "simple":
      return simplify(baseSummary);
    case "technical":
      return compress(baseSummary);
    case "story":
      return preserveNarrativeTone(baseSummary);
    default:
      return baseSummary;
  }
}