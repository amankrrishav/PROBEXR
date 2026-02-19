export function generateSummary(text) {
  const trimmed = text.trim();
  if (!trimmed) return "";

  const sentences = trimmed.match(/[^.!?]+[.!?]+/g) || [trimmed];
  
  // Get first two sentences or first 150 characters
  if (sentences.length >= 2) {
    const summary = sentences.slice(0, 2).join(" ");
    return summary.length > 150 ? summary.substring(0, 150) + "..." : summary;
  }
  
  const firstSentence = sentences[0] || trimmed;
  return firstSentence.length > 150 
    ? firstSentence.substring(0, 150) + "..." 
    : firstSentence;
}
