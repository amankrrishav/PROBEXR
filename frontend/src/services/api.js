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

/**
 * POST /api/ingest/url — { url } -> Document
 */
export async function ingestUrl(url) {
  return request("/api/ingest/url", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

/**
 * POST /api/synthesis/ — { document_ids, prompt } -> Synthesis
 */
export async function synthesizeDocuments(documentIds, prompt = null) {
  return request("/api/synthesis/", {
    method: "POST",
    body: JSON.stringify({ document_ids: documentIds, prompt }),
  });
}

/**
 * POST /api/chat/ — { document_id, message, session_id } -> ChatMessage
 */
export async function sendChatMessage(documentId, message, sessionId = null) {
  const body = { document_id: documentId, message };
  if (sessionId) {
    body.session_id = sessionId;
  }
  return request("/api/chat/", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/**
 * POST /api/flashcards/ — { document_id, count } -> FlashcardSet
 */
export async function generateFlashcards(documentId, count = 10) {
  return request("/api/flashcards/", {
    method: "POST",
    body: JSON.stringify({ document_id: documentId, count }),
  });
}

/**
 * POST /api/tts/ — { document_id, provider } -> AudioSummary
 */
export async function generateAudioSummary(documentId, provider = "openai") {
  return request("/api/tts/", {
    method: "POST",
    body: JSON.stringify({ document_id: documentId, provider }),
  });
}
