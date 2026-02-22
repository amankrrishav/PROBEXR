/**
 * API — backend endpoints. Add new feature endpoints here (or in separate modules).
 * Uses client.js for base URL and request helper. Matches backend contract.
 */
import { request } from "./client.js";

/**
 * POST /summarize — { text } → { summary }
 */
export async function summarizeText(text) {
  const data = await request("/summarize", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
  return data.summary;
}

/**
 * GET / — health check. Use for future: ping backend, show mode (extractive vs groq).
 */
export async function getHealth() {
  return request("/");
}
