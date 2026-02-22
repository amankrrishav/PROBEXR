/**
 * API client — base URL and request helper. Add new endpoints in api.js (or separate modules).
 * Matches backend: same base URL, JSON request/response, parse errors.
 */
import { config } from "../config.js";

export function getBaseUrl() {
  return config.apiBaseUrl.replace(/\/$/, "");
}

/**
 * Parse FastAPI error detail (string or validation array).
 */
export function parseErrorDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (first?.msg != null) return first.msg;
    if (typeof first === "string") return first;
  }
  return null;
}

/**
 * Generic request helper. Use for new endpoints (e.g. GET /health, POST /api/url-fetch).
 * Applies request timeout to avoid hanging on slow backend.
 */
export async function request(path, options = {}) {
  const { requestTimeoutMs } = config;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), requestTimeoutMs);

  const url = `${getBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;
  const init = {
    ...options,
    signal: options.signal ?? controller.signal,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  };

  try {
    const res = await fetch(url, init);
    clearTimeout(timeoutId);

    if (!res.ok) {
      let message = res.statusText || "Request failed";
      try {
        const data = await res.json();
        message = parseErrorDetail(data.detail) || data.error || message;
      } catch {
        // ignore
      }
      throw new Error(message);
    }

    return res.json();
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new Error("Request timed out. Try again or use a shorter text.");
    }
    throw err;
  }
}
