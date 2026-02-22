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
 */
export async function request(path, options = {}) {
  const url = `${getBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

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
}
