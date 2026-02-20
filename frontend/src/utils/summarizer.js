export async function generateAdaptiveSummary(text) {
  const response = await fetch("http://127.0.0.1:8000/summarize", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ text })
  });

  if (!response.ok) {
    throw new Error("ML summarizer failed");
  }

  const data = await response.json();
  return data.summary;
}