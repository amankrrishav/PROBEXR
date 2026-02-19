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
  const [error, setError] = useState(null);

  // ==============================
  // 1️⃣ Resolve Input
  // ==============================
  async function resolveInput() {
    const trimmed = text.trim();

    if (!trimmed) {
      throw new Error("Input cannot be empty.");
    }

    if (mode === "url") {
      return await fetchTextFromUrl(trimmed);
    }

    return trimmed;
  }

  // ==============================
  // 2️⃣ Full Analysis Pipeline
  // ==============================
  async function runPipeline(inputText) {
    const wordCount = inputText.split(/\s+/).length;

    if (wordCount < 50) {
      throw new Error("Minimum 50 words required.");
    }

    const reading = getReadingTime(inputText);
    const difficulty = getDifficulty(inputText);

    // 🔥 Calls FastAPI ML backend
    const summary = await generateAdaptiveSummary(inputText);

    return { reading, difficulty, summary };
  }

  // ==============================
  // 3️⃣ Analyze Handler
  // ==============================
  async function handleAnalyze() {
    if (loading) return;

    setLoading(true);
    setError(null);
    setCopied(false);

    try {
      const inputText = await resolveInput();
      const output = await runPipeline(inputText);
      setResult(output);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  // ==============================
  // 4️⃣ Copy Handler
  // ==============================
  function handleCopy() {
    if (!result) return;

    const snippet =
      "📖 " +
      result.reading.average +
      " read · Difficulty " +
      result.difficulty.score +
      "/10 (" +
      result.difficulty.label +
      ")\n💡 \"" +
      result.summary +
      "\"";

    navigator.clipboard.writeText(snippet);

    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  // ==============================
  // UI
  // ==============================
  return (
    <div className="app">
      <header>
        <h1>ReadPulse</h1>
        <p>Paste text or URL — neural summarizer engine.</p>
      </header>

      {error && (
        <div style={{ color: "#ef4444", marginBottom: "16px" }}>
          {error}
        </div>
      )}

      {!result && (
        <>
          <div style={{ marginBottom: "12px", display: "flex", gap: "8px" }}>
            <button
              onClick={() => setMode("text")}
              disabled={loading}
            >
              Paste Text
            </button>
            <button
              onClick={() => setMode("url")}
              disabled={loading}
            >
              From URL
            </button>
          </div>

          {mode === "text" ? (
            <textarea
              rows={12}
              placeholder="Paste at least 50 words..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={loading}
            />
          ) : (
            <input
              type="url"
              placeholder="https://example.com/article"
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={loading}
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
          <div className="section">
            <h2>Reading Time</h2>
            <p>Casual: <span className="highlight">{result.reading.casual}</span></p>
            <p>Average: <span className="highlight">{result.reading.average}</span></p>
            <p>Fast: <span className="highlight">{result.reading.fast}</span></p>
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

            {result.difficulty.topWords?.length > 0 && (
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

          <button
            onClick={() => {
              setResult(null);
              setText("");
              setError(null);
            }}
          >
            Analyze Another
          </button>
        </div>
      )}
    </div>
  );
}