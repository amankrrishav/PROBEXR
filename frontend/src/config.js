/**
 * Frontend config — single place for env and constants (like backend app/config.py).
 * Add new keys here as you add features.
 */

export const config = {
  appName: import.meta.env.VITE_APP_NAME || "PROBEXR",
  appVersion: import.meta.env.VITE_APP_VERSION || "1.0.0",
  apiBaseUrl: import.meta.env.VITE_API_URL || "https://readpulse.onrender.com/api/v1",

  // Request timeout (ms). Prevents hanging on slow backend.
  requestTimeoutMs: Number(import.meta.env.VITE_REQUEST_TIMEOUT_MS) || 120000,

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
