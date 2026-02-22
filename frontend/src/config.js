/**
 * Frontend config — single place for env and constants (like backend app/config.py).
 * Add new keys here as you add features.
 */

export const config = {
  appName: import.meta.env.VITE_APP_NAME || "ReadPulse",
  apiBaseUrl: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000",

  // Summarizer (must match backend SUMMARIZE_MIN_WORDS when set)
  summarizer: {
    minWords: Number(import.meta.env.VITE_SUMMARIZE_MIN_WORDS) || 30,
  },

  // Loading messages (shown while backend is processing)
  loadingMessages: [
    "Analyzing structure…",
    "Ranking sentences…",
    "Removing redundancy…",
    "Finalizing summary…",
  ],
};
