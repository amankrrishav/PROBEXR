/**
 * Frontend config — single place for env and constants (like backend app/config.py).
 * Add new keys here as you add features. Subscription-ready: add showUpgradeCta, plan, etc. when you add billing.
 */

export const config = {
  appName: import.meta.env.VITE_APP_NAME || "ReadPulse",
  appVersion: import.meta.env.VITE_APP_VERSION || "1.0.0",
  apiBaseUrl: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000",

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

  // Future: subscription / plans — show upgrade CTA, limit reached, etc.
  subscription: {
    enabled: import.meta.env.VITE_SUBSCRIPTION_ENABLED === "true",
    showUpgradeCta: false, // Set true when you add pricing page / paywall
  },
};
