// src/services/api.js

const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function parseErrorDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (first?.msg != null) return first.msg;
    if (typeof first === "string") return first;
  }
  return "Summarization failed";
}

export async function summarizeText(text) {
  const response = await fetch(`${BASE_URL}/summarize`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    let message = "Summarization failed";
    try {
      const errorData = await response.json();
      message = parseErrorDetail(errorData.detail) || message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  const data = await response.json();
  return data.summary;
}