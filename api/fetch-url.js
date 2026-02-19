export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { url } = req.body;
  if (!url) {
    return res.status(400).json({ error: "No URL provided" });
  }

  try {
    // Only handle Wikipedia URLs
    if (url.includes("wikipedia.org")) {
      const titleMatch = url.match(/wiki\/([^#]+)/);
      if (!titleMatch) {
        return res.status(400).json({ error: "Invalid Wikipedia URL" });
      }

      const title = decodeURIComponent(titleMatch[1]);

      const wikiRes = await fetch(
        `https://en.wikipedia.org/api/rest_v1/page/summary/${title}`,
        {
          headers: {
            "User-Agent": "ReadPulseApp/1.0"
          }
        }
      );

      const data = await wikiRes.json();

      if (!data.extract) {
        return res.status(400).json({ error: "Could not extract content." });
      }

      return res.status(200).json({ text: data.extract });
    }

    // Fallback for non-wikipedia URLs
    const response = await fetch(url);
    const html = await response.text();

    const text = html
      .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, "")
      .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, "")
      .replace(/<[^>]+>/g, " ")
      .replace(/\s{2,}/g, " ")
      .trim();

    if (text.length < 100) {
      return res.status(400).json({ error: "Could not extract enough text." });
    }

    return res.status(200).json({ text });

  } catch (err) {
    return res.status(500).json({ error: "Failed to fetch URL." });
  }
}