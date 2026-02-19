import { useState } from "react";
import { getReadingTime } from "./utils/readingTime";
import { getDifficulty } from "./utils/difficulty";
import DifficultyBar from "./components/DifficultyBar";

export default function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  async function handleAnalyze() {
    if (text.trim().split(/\s+/).length < 50) {
      alert("Minimum 50 words required.");
      return;
    }

    setLoading(true);

    // Core logic (instant)
    const reading = getReadingTime(text);
    const difficulty = getDifficulty(text);

    // AI call
    let summary = "—";
    try {
      const res = await fetch("/api/summarize", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text }),
      });

      const data = await res.json();
      summary = data.summary || "Summary unavailable.";
    } catch {
      summary = "Summary unavailable.";
    }

    setResult({ reading, difficulty, summary });
    setLoading(false);
  }

  function handleCopy() {
    if (!result) return;

    const snippet = `📖 ${result.reading.average} read · Difficulty ${result.difficulty.score}/10 (${result.difficulty.label})
💡 "${result.summary}"`;

    navigator.clipboard.writeText(snippet);

    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="app">
      <header>
        <h1>ReadPulse</h1>
        <p>Paste any text — get reading time, difficulty, and summary.</p>
      </header>

      {!result && (
        <>
          <textarea
            rows={12}
            placeholder="Paste at least 50 words..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <button onClick={handleAnalyze} disabled={loading}>
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </>
      )}

      {result && (
        <div className="results">
          <div className="section">
            <h2>Reading Time</h2>
            <p>
              Casual:{" "}
              <span className="highlight">
                {result.reading.casual}
              </span>
            </p>
            <p>
              Average:{" "}
              <span className="highlight">
                {result.reading.average}
              </span>
            </p>
            <p>
              Fast:{" "}
              <span className="highlight">
                {result.reading.fast}
              </span>
            </p>
          </div>

          <div className="section">
            <h2>Difficulty</h2>
            <p>
              <span
                style={{
                  color: result.difficulty.color,
                  fontWeight: 600,
                }}
              >
                {result.difficulty.score}/10 — {result.difficulty.label}
              </span>
            </p>

            <DifficultyBar score={result.difficulty.score} />

            {result.difficulty.topWords.length > 0 && (
              <div
                style={{
                  marginTop: "16px",
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "6px",
                }}
              >
                {result.difficulty.topWords.map((word) => (
                  <span
                    key={word}
                    style={{
                      background: "#f4f3f0",
                      border: "1px solid #e8e5df",
                      borderRadius: "6px",
                      padding: "4px 10px",
                      fontSize: "0.8rem",
                      fontWeight: "500",
                      color: "#555",
                    }}
                  >
                    {word}
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="section">
            <h2>Summary</h2>
            <p>{result.summary}</p>
          </div>

          <button onClick={handleCopy}>
            {copied ? "Copied ✓" : "Copy Result"}
          </button>

          <button onClick={() => setResult(null)}>
            Analyze Another
          </button>
        </div>
      )}
    </div>
  );
}