// src/services/api.js

const BASE_URL = "http://127.0.0.1:8000";

export async function summarizeText(text) {
  const response = await fetch(`${BASE_URL}/summarize`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Summarization failed");
  }

  const data = await response.json();
  return data.summary;
}