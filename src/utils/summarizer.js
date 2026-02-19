export function generateSummary(text) {
  const trimmed = text.trim();
  if (!trimmed) return "";

  const sentences = trimmed.match(/[^.!?]+[.!?]+/g) || [trimmed];
  
  // If the text is short, return first sentence
  if (sentences.length <= 2) {
    return sentences[0].trim();
  }

  // Take first and last sentence for a simple summary
  const firstSentence = sentences[0].trim();
  
  // Limit summary length
  if (firstSentence.length > 150) {
    return firstSentence.substring(0, 147) + "...";
  }

  return firstSentence;
}
