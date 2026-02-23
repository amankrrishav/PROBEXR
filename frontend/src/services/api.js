/**
 * API — backend endpoints. Add new feature endpoints here (or in separate modules).
 * Uses client.js for base URL and request helper. Matches backend contract.
 */
import { request } from "./client.js";

/**
 * POST /summarize — { text } → { summary, quality, usage_today, limit }
 */
export async function summarizeText(text) {
  const data = await request("/summarize", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
  return {
    summary: data.summary,
    quality: data.quality ?? "full",
    usageToday: data.usage_today ?? null,
    limit: data.limit ?? null,
  };
}

/**
 * GET / — health check. Use for future: ping backend, show mode (extractive vs groq).
 */
export async function getHealth() {
  return request("/");
}
