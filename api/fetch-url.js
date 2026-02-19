export default async function handler(req, res) {
  try {
    if (req.method !== "POST") {
      return res.status(405).json({ error: "Method not allowed" });
    }

    const { url } = req.body || {};

    if (!url || typeof url !== "string") {
      return res.status(400).json({ error: "No URL provided" });
    }

    // Basic URL validation
    if (!url.startsWith("http")) {
      return res.status(400).json({ error: "Invalid URL format" });
    }

    // ============================
    // 1️⃣ Wikipedia Fast Path
    // ============================

    if (url.includes("wikipedia.org")) {
      const titleMatch = url.match(/wiki\/([^#?]+)/);

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

      if (!wikiRes.ok) {
        return res.status(400).json({ error: "Wikipedia fetch failed." });
      }

      const data = await wikiRes.json();

      if (!data.extract) {
        return res.status(400).json({ error: "No extract found." });
      }

      return res.status(200).json({ text: data.extract });
    }

    // ============================
    // 2️⃣ Generic Website Fallback
    // ============================

    const response = await fetch(url, {
      headers: {
        "User-Agent": "ReadPulseBot/1.0"
      }
    });

    if (!response.ok) {
      return res.status(400).json({ error: "Failed to fetch website." });
    }

    const html = await response.text();

    // Strip scripts, styles, and tags
    const text = html
      .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, "")
      .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, "")
      .replace(/<noscript[^>]*>[\s\S]*?<\/noscript>/gi, "")
      .replace(/<[^>]+>/g, " ")
      .replace(/\s{2,}/g, " ")
      .trim();

    if (text.length < 150) {
      return res.status(400).json({
        error: "Could not extract sufficient readable content."
      });
    }

    return res.status(200).json({ text });

  } catch (err) {
    console.error("Fetch error:", err);
    return res.status(500).json({
      error: "Internal server error while fetching URL."
    });
  }
}