export function getReadingTime(text) {
  const trimmed = text.trim();
  if (!trimmed) return null;

  const words = trimmed.split(/\s+/).length;

  function toDisplay(wpm) {
    const mins = Math.ceil(words / wpm);
    return mins < 1 ? "< 1 min" : `${mins} min`;
  }

  return {
    words,
    casual: toDisplay(180),
    average: toDisplay(238),
    fast: toDisplay(350),
  };
}