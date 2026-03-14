/**
 * API — backend endpoints. Add new feature endpoints here (or in separate modules).
 * Uses client.js for base URL and request helper. Matches backend contract.
 */
import { request, streamRequest } from "./client.js";

/**
 * POST /summarize — { text, length } → { summary, key_takeaways, compression_ratio, ... }
 */
export async function summarizeText(text, length = "standard", mode = "paragraph", tone = "neutral", keywords = []) {
  return request("/summarize", {
    method: "POST",
    body: JSON.stringify({ text, length, mode, tone, keywords }),
  });
}

/**
 * POST /summarize/stream — SSE streaming summarization with metadata.
 * @param {string} text
 * @param {string} length - "brief" | "standard" | "detailed"
 * @param {Function} onToken - called with each content delta
 * @param {Function} onDone - called with metadata on completion
 * @param {Function} onTakeaways - called with takeaways array
 * @param {Function} onError - called with error string
 * @param {AbortController} [abortController]
 */
export function summarizeTextStream(text, length, onToken, onDone, onTakeaways, onError, abortController, mode = "paragraph", tone = "neutral", keywords = []) {
  return streamRequest(
    "/summarize/stream",
    { method: "POST", body: JSON.stringify({ text, length, mode, tone, keywords }) },
    onToken,
    onDone,
    onTakeaways,
    onError,
    abortController,
  );
}

/**
 * GET / — health check.
 */
export async function getHealth() {
  return request("/");
}

/**
 * POST /api/ingest/url — { url } -> Document
 */
export async function ingestUrl(url) {
  return request("/ingest/url", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

/**
 * POST /api/ingest/text — { text, title } -> Document
 */
export async function ingestText(text, title = "Pasted Text") {
  return request("/ingest/text", {
    method: "POST",
    body: JSON.stringify({ text, title }),
  });
}

/**
 * POST /api/synthesis/ — { document_ids, prompt } -> Synthesis
 */
export async function synthesizeDocuments(documentIds, prompt = null) {
  return request("/synthesis/", {
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
  return request("/chat/", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/**
 * POST /chat/stream — SSE streaming chat.
 * @param {number} documentId
 * @param {string} message
 * @param {number|null} sessionId
 * @param {Function} onToken
 * @param {Function} onDone
 * @param {Function} onError
 * @param {AbortController} [abortController]
 */
export function sendChatMessageStream(documentId, message, sessionId, onToken, onDone, onError, abortController) {
  const body = { document_id: documentId, message };
  if (sessionId) {
    body.session_id = sessionId;
  }
  return streamRequest(
    "/chat/stream",
    { method: "POST", body: JSON.stringify(body) },
    onToken,
    onDone,
    null, // no onTakeaways for chat
    onError,
    abortController,
  );
}

/**
 * POST /api/flashcards/ — { document_id, count } -> FlashcardSet
 */
export async function generateFlashcards(documentId, count = 10) {
  return request("/flashcards/", {
    method: "POST",
    body: JSON.stringify({ document_id: documentId, count }),
  });
}

/**
 * POST /api/tts/ — { document_id, provider } -> AudioSummary
 */
export async function generateAudioSummary(documentId, provider = "openai") {
  return request("/tts/", {
    method: "POST",
    body: JSON.stringify({ document_id: documentId, provider }),
  });
}

/**
 * GET /api/tts/status — Check if TTS is available
 */
export async function getTTSStatus() {
  return request("/tts/status");
}

/**
 * GET /api/documents/ — List authenticated user's documents (paginated)
 * @param {number} page
 * @param {number} perPage
 */
export async function getDocuments(page = 1, perPage = 20) {
  return request(`/documents/?page=${page}&per_page=${perPage}`);
}

/**
 * DELETE /api/documents/:id — Delete a document
 * @param {number} documentId
 */
export async function deleteDocument(documentId) {
  return request(`/documents/${documentId}`, {
    method: "DELETE",
  });
}

/**
 * GET /api/analytics/dashboard — Reading analytics for the authenticated user
 */
export async function getAnalytics() {
  return request("/analytics/dashboard");
}
