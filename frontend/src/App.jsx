import { useEffect, useState } from "react";

export default function App() {
  const MIN_WORDS = 30;

  const [text, setText] = useState("");
  const [dark, setDark] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [hasSummary, setHasSummary] = useState(false);
  const [summaryText, setSummaryText] = useState("");
  const [displayedText, setDisplayedText] = useState("");

  // =====================
  // Counts
  // =====================
  const wordCount = text.trim()
    ? text.trim().split(/\s+/).length
    : 0;

  const charCount = text.length;

  // =====================
  // Keyboard Shortcut
  // =====================
  function handleKeyDown(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      handleSummarize();
    }
  }

  // =====================
  // Backend Call
  // =====================
  async function handleSummarize() {
    if (loading) return;

    if (wordCount < MIN_WORDS) {
      setError(`Minimum ${MIN_WORDS} words required.`);
      return;
    }

    setError(null);
    setLoading(true);
    setHasSummary(false);

    try {
      const response = await fetch("http://127.0.0.1:8000/summarize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ text })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Backend error");
      }

      setSummaryText(data.summary);
      setHasSummary(true);

    } catch (err) {
      setError(err.message || "Failed to connect to backend.");
    } finally {
      setLoading(false);
    }
  }

  // =====================
  // Typing Effect (Paragraph)
  // =====================
  useEffect(() => {
    if (!summaryText) return;

    setDisplayedText("");
    let index = 0;

    const interval = setInterval(() => {
      setDisplayedText(prev => prev + summaryText[index]);
      index++;

      if (index >= summaryText.length) {
        clearInterval(interval);
      }
    }, 6);

    return () => clearInterval(interval);
  }, [summaryText]);

  // =====================
  // Theme Handling
  // =====================
  useEffect(() => {
    const saved = localStorage.getItem("theme");
    if (saved === "dark") {
      setDark(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  function toggleTheme() {
    if (dark) {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    } else {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    }
    setDark(!dark);
  }

  function resetWorkspace() {
    setHasSummary(false);
    setSummaryText("");
    setDisplayedText("");
    setText("");
    setError(null);
  }

  return (
    <div className="h-screen flex bg-[#F8F7F4] text-[#1A1A2E] dark:bg-[#0a0a0a] dark:text-white transition-colors duration-300">

      {/* Sidebar */}
      <aside className="w-80 bg-white dark:bg-[#111111] border-r border-gray-200 dark:border-gray-800 flex flex-col">

        <div className="px-6 py-6 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center">
          <div className="text-lg font-semibold tracking-tight">
            ReadPulse
          </div>

          <button
            onClick={toggleTheme}
            className="text-xs px-3 py-1 rounded-md bg-gray-200 dark:bg-gray-800 hover:opacity-80 transition"
          >
            {dark ? "Light" : "Dark"}
          </button>
        </div>

        <div className="px-6 py-6">
          <button
            onClick={resetWorkspace}
            className="w-full px-6 py-2.5 rounded-full text-sm font-medium bg-black text-white dark:bg-white dark:text-black hover:opacity-90 transition"
          >
            + New Summary
          </button>
        </div>

      </aside>

      {/* Workspace */}
      <main className="flex-1 overflow-y-auto">

        <div
          className={`px-12 py-16 transition-all duration-500 ${
            hasSummary
              ? "grid grid-cols-2 gap-12"
              : "max-w-3xl mx-auto"
          }`}
        >

          {/* LEFT — Editor */}
          <div>

            {!hasSummary && (
              <>
                <h1 className="text-3xl font-semibold tracking-tight mb-3">
                  Extract signal. Ignore noise.
                </h1>

                <p className="text-gray-500 dark:text-gray-400 mb-10">
                  Paste text or URL. Get the point instantly.
                </p>
              </>
            )}

            {error && (
              <div className="mb-6 text-sm text-red-500">
                {error}
              </div>
            )}

            <div className="bg-white dark:bg-[#121212] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">

              <textarea
                rows={hasSummary ? 6 : 8}
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Paste article, research, or blog post..."
                className="w-full resize-none outline-none text-sm leading-relaxed bg-transparent"
              />

              <div className="flex justify-between items-center mt-6">

                <div className="text-xs text-gray-400">
                  {wordCount} words · {charCount} characters
                </div>

                <button
                  onClick={handleSummarize}
                  disabled={loading}
                  className="px-6 py-2.5 rounded-full text-sm font-medium bg-black text-white dark:bg-white dark:text-black hover:opacity-90 transition disabled:opacity-50"
                >
                  {loading ? "Analyzing…" : "Summarize"}
                </button>

              </div>
            </div>
          </div>

          {/* RIGHT — Summary */}
          {hasSummary && (
            <div className="bg-white dark:bg-[#121212] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">

              <h3 className="text-xs uppercase tracking-wider text-gray-400 mb-6">
                Summary
              </h3>

              <p className="text-sm leading-relaxed whitespace-pre-line">
                {displayedText}
              </p>

            </div>
          )}

        </div>
      </main>
    </div>
  );
}