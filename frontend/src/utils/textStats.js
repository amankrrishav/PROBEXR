export function getTextStats(text) {
  const words = text.trim().split(/\s+/).length;
  const chars = text.replace(/\s/g, "").length;
  const sentences = (text.match(/[^.!?]+[.!?]+/g) || []).length;
  const paragraphs = text.split(/\n\s*\n/).filter(Boolean).length;

  return { words, chars, sentences, paragraphs };
}