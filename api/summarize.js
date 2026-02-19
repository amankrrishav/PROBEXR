export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { text } = req.body;

  if (!text || text.trim().length < 50) {
    return res.status(400).json({ error: "Text too short" });
  }

  // TEMP MOCK RESPONSE (since no API key yet)
  return res.status(200).json({
    summary: "AI-generated summary will appear here once API is connected."
  });
}