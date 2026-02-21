import { useEffect, useState } from "react";
import { summarizeText } from "./services/api";

import Sidebar from "./features/layout/Sidebar";
import Editor from "./features/summarizer/Editor";
import OutputCard from "./features/summarizer/OutputCard";

export default function App() {
  const MIN_WORDS = 30;

  const [text, setText] = useState("");
  const [dark, setDark] = useState(false);

  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState(null);

  const [hasSummary, setHasSummary] = useState(false);
  const [summaryText, setSummaryText] = useState("");

  // =====================
  // Loading Messages
  // =====================
  const loadingMessages = [
    "Analyzing structure…",
    "Ranking sentences…",
    "Removing redundancy…",
    "Finalizing summary…"
  ];

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

    try {
      setError(null);
      setLoading(true);
      setHasSummary(false);

      const summary = await summarizeText(text);

      setSummaryText(summary);
      setHasSummary(true);
    } catch (err) {
      setError(err.message || "Failed to connect to backend.");
    } finally {
      setLoading(false);
    }
  }

  // =====================
  // Rotating Loading Effect
  // =====================
  useEffect(() => {
    if (!loading) return;

    setLoadingStep(0);
    let step = 0;

    const interval = setInterval(() => {
      step = (step + 1) % loadingMessages.length;
      setLoadingStep(step);
    }, 900);

    return () => clearInterval(interval);
  }, [loading]);

  // =====================
  // Theme Load
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

  // =====================
  // Reset
  // =====================
  function resetWorkspace() {
    setHasSummary(false);
    setSummaryText("");
    setText("");
    setError(null);
  }

  // =====================
  // UI
  // =====================
  return (
    <div className="h-screen flex bg-[#F8F7F4] text-[#1A1A2E] dark:bg-[#0a0a0a] dark:text-white transition-colors duration-300">

      <Sidebar
        dark={dark}
        toggleTheme={toggleTheme}
        resetWorkspace={resetWorkspace}
      />

      <main className="flex-1 overflow-y-auto">
        <div
          className={`px-12 py-16 transition-all duration-500 ${
            hasSummary
              ? "grid grid-cols-2 gap-12"
              : "max-w-3xl mx-auto"
          }`}
        >
          <Editor
            text={text}
            setText={setText}
            loading={loading}
            loadingMessage={loadingMessages[loadingStep]}
            error={error}
            wordCount={wordCount}
            charCount={charCount}
            hasSummary={hasSummary}
            onSummarize={handleSummarize}
            handleKeyDown={handleKeyDown}
          />

          {hasSummary && (
            <OutputCard summaryText={summaryText} />
          )}
        </div>
      </main>
    </div>
  );
}