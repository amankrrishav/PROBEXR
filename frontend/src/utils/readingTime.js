// ==============================
// Reading Time Feature Engine
// ==============================

const SPEEDS = {
  casual: 180,
  average: 238,
  fast: 350,
};

function calculateMinutes(words, wpm) {
  return words / wpm;
}

function formatMinutes(minutes) {
  const rounded = Math.ceil(minutes);
  return rounded < 1 ? "< 1 min" : `${rounded} min`;
}

export function getReadingTime(text) {
  const trimmed = text?.trim();
  if (!trimmed) return null;

  const words = trimmed.split(/\s+/).length;

  const casualMin = calculateMinutes(words, SPEEDS.casual);
  const averageMin = calculateMinutes(words, SPEEDS.average);
  const fastMin = calculateMinutes(words, SPEEDS.fast);

  return {
    // Raw ML-ready features
    words,
    casualMinutes: casualMin,
    averageMinutes: averageMin,
    fastMinutes: fastMin,

    // UI formatted values
    casual: formatMinutes(casualMin),
    average: formatMinutes(averageMin),
    fast: formatMinutes(fastMin),
  };
}