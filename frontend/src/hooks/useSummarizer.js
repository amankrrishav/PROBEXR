/**
 * Summarizer feature state and logic — keeps App thin. Add new feature hooks the same way.
 */
import { useEffect, useState } from "react";
import { config } from "../config.js";
import { summarizeText } from "../services/api.js";

const MIN_WORDS = config.summarizer.minWords;
const LOADING_MESSAGES = config.loadingMessages;

export function useSummarizer() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState(null);
  const [hasSummary, setHasSummary] = useState(false);
  const [summaryText, setSummaryText] = useState("");
  const [quality, setQuality] = useState("full");

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const charCount = text.length;

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
      const result = await summarizeText(text);
      setSummaryText(result.summary);
      setQuality(result.quality || "full");
      setHasSummary(true);
    } catch (err) {
      setError(err.message || "Failed to connect to backend.");
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      handleSummarize();
    }
  }

  function reset() {
    setHasSummary(false);
    setSummaryText("");
    setText("");
    setError(null);
  }

  // Rotate loading message while loading
  useEffect(() => {
    if (!loading) return;
    setLoadingStep(0);
    let step = 0;
    const interval = setInterval(() => {
      step = (step + 1) % LOADING_MESSAGES.length;
      setLoadingStep(step);
    }, 900);
    return () => clearInterval(interval);
  }, [loading]);

  return {
    text,
    setText,
    loading,
    loadingMessage: LOADING_MESSAGES[loadingStep],
    error,
    wordCount,
    charCount,
    hasSummary,
    summaryText,
    quality,
    onSummarize: handleSummarize,
    handleKeyDown,
    reset,
  };
}
