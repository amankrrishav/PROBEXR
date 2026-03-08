/**
 * API client — base URL and request helper. Add new endpoints in api.js (or separate modules).
 * Matches backend: same base URL, JSON request/response, parse errors.
 * Includes automatic 401 retry with refresh token rotation.
 */
import { config } from "../config.js";

// In-flight refresh promise — prevents concurrent refresh calls
let _refreshPromise = null;

async function _attemptTokenRefresh() {
  if (_refreshPromise) return _refreshPromise;
  _refreshPromise = fetch(`${getBaseUrl()}/auth/refresh`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  }).then((res) => {
    _refreshPromise = null;
    return res.ok;
  }).catch(() => {
    _refreshPromise = null;
    return false;
  });
  return _refreshPromise;
}


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
  const skipRefresh = options._skipAutoRefresh;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), requestTimeoutMs);

  const url = `${getBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;

  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };
  // Remove internal flag before passing to fetch
  // eslint-disable-next-line no-unused-vars
  const { _skipAutoRefresh, ...fetchOptions } = options;
  const init = {
    ...fetchOptions,
    credentials: fetchOptions.credentials ?? "include",
    signal: fetchOptions.signal ?? controller.signal,
    headers,
  };

  try {
    let res = await fetch(url, init);
    clearTimeout(timeoutId);

    // Auto-retry on 401: attempt token refresh, then retry once
    if (res.status === 401 && !skipRefresh) {
      const refreshed = await _attemptTokenRefresh();
      if (refreshed) {
        const retryController = new AbortController();
        const retryTimeout = setTimeout(() => retryController.abort(), requestTimeoutMs);
        try {
          res = await fetch(url, {
            ...init,
            signal: retryController.signal,
          });
          clearTimeout(retryTimeout);
        } catch (retryErr) {
          clearTimeout(retryTimeout);
          throw retryErr;
        }
      }
    }

    if (!res.ok) {
      let message = res.statusText || "Request failed";
      const contentType = res.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        try {
          const data = await res.json();
          message = parseErrorDetail(data.detail) || data.error || message;
        } catch {
          // ignore
        }
      }
      throw new Error(message);
    }

    // 204 No Content (e.g. DELETE) — no body to parse
    if (res.status === 204) return null;

    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return res.json();
    }
    return res.text();
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new Error("Request timed out. Try again or use a shorter text.");
    }
    throw err;
  }
}

/**
 * SSE streaming request helper. Consumes text/event-stream from the backend.
 *
 * @param {string} path - API path (e.g. "/summarize/stream")
 * @param {Object} options - fetch options (method, body, etc.)
 * @param {Function} onToken - called with each content delta string
 * @param {Function} onDone - called with metadata object when stream completes
 * @param {Function} onError - called with error message string
 * @param {AbortController} [abortController] - optional controller for cancellation
 * @returns {Promise<void>}
 */
export async function streamRequest(path, options, onToken, onDone, onTakeaways, onError, abortController) {
  const controller = abortController || new AbortController();
  const url = `${getBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;

  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  try {
    let res = await fetch(url, {
      ...options,
      credentials: options.credentials ?? "include",
      signal: controller.signal,
      headers,
    });

    // Auto-retry on 401: attempt token refresh, then retry once
    if (res.status === 401) {
      const refreshed = await _attemptTokenRefresh();
      if (refreshed) {
        res = await fetch(url, {
          ...options,
          credentials: options.credentials ?? "include",
          signal: controller.signal,
          headers,
        });
      }
    }

    if (!res.ok) {
      let message = res.statusText || "Stream request failed";
      const contentType = res.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        try {
          const data = await res.json();
          message = parseErrorDetail(data.detail) || data.error || message;
        } catch {
          // ignore
        }
      }
      onError(message);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data: ")) continue;

        const dataStr = trimmed.slice(6);

        try {
          const parsed = JSON.parse(dataStr);
          if (parsed.error) {
            onError(parsed.error);
            return;
          }
          if (parsed.takeaways && onTakeaways) {
            onTakeaways(parsed.takeaways);
            continue;
          }
          if (parsed.done) {
            onDone(parsed);
            return;
          }
          if (parsed.token != null) {
            onToken(parsed.token);
          }
        } catch {
          // Non-JSON data line — skip
        }
      }
    }

    // Process any remaining buffer
    if (buffer.trim().startsWith("data: ")) {
      try {
        const parsed = JSON.parse(buffer.trim().slice(6));
        if (parsed.done) {
          onDone(parsed);
        } else if (parsed.token != null) {
          onToken(parsed.token);
        }
      } catch {
        // ignore
      }
    }
  } catch (err) {
    if (err.name === "AbortError") {
      // User cancelled — not an error
      return;
    }
    onError(err.message || "Stream connection failed");
  }
}
