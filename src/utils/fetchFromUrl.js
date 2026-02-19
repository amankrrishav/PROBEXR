export async function fetchTextFromUrl(url) {
  const res = await fetch("/api/fetch-url", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ url })
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || "Failed to fetch URL.");
  }

  return data.text;
}