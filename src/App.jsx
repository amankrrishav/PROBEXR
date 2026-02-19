import { useState } from "react";
import { getReadingTime } from "./utils/readingTime";
import { getDifficulty } from "./utils/difficulty";
import DifficultyBar from "./components/DifficultyBar";
import { generateAdaptiveSummary } from "./utils/summarizer";
import { fetchTextFromUrl } from "./utils/fetchFromUrl";

export default function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [mode, setMode] = useState("text");

  async function handleAnalyze() {
    if (!text.trim()) return;

    setLoading(true);
    setCopied(false);

    let finalText = text;

    try {
      // URL Mode Handling
      if (mode === "url") {
        finalText = await fetchTextFromUrl(text);
      }

      // Minimum word check
      if (finalText.trim().split(/\s+/).length < 50) {
        alert("Minimum 50 words required.");
        setLoading(false);
        return;
      }

      // Core Analysis
      const reading = getReadingTime(finalText);
      const difficulty = getDifficulty(finalText);

      // Adaptive Summary
      const summary = generateAdaptiveSummary(
        finalText,
        difficulty.score
      );

      setResult({ reading, difficulty, summary });

    } catch (err) {
      alert(err.message || "Something went wrong.");
    }

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
        <p>Paste text or URL — get reading time, difficulty, and adaptive summary.</p>
      </header>

      {!result && (
        <>
          <div style={{ marginBottom: "12px", display: "flex", gap: "8px" }}>
            <button onClick={() => setMode("text")}>
              Paste Text
            </button>
            <button onClick={() => setMode("url")}>
              From URL
            </button>
          </div>

          {mode === "text" ? (
            <textarea
              rows={12}
              placeholder="Paste at least 50 words..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          ) : (
            <input
              type="url"
              placeholder="https://example.com/article"
              value={text}
              onChange={(e) => setText(e.target.value)}
              style={{
                width: "100%",
                padding: "14px",
                borderRadius: "12px",
                border: "1.5px solid #e2dfd8",
                fontSize: "1rem",
              }}
            />
          )}

          <button onClick={handleAnalyze} disabled={loading}>
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </>
      )}

      {result && (
        <div className="results">
          {/* Reading Time */}
          <div className="section">
            <h2>Reading Time</h2>
            <p>
              Casual: <span className="highlight">{result.reading.casual}</span>
            </p>
            <p>
              Average: <span className="highlight">{result.reading.average}</span>
            </p>
            <p>
              Fast: <span className="highlight">{result.reading.fast}</span>
            </p>
          </div>

          {/* Difficulty */}
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

          {/* Summary */}
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