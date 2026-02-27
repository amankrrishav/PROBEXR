/**
 * Summarizer feature state and logic — keeps App thin. Add new feature hooks the same way.
 */
import { useEffect, useState, useCallback } from "react";
import { config } from "../config.js";
import { summarizeText, ingestUrl } from "../services/api.js";

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
  const [isUrlMode, setIsUrlMode] = useState(false);
  const [url, setUrl] = useState("");
  const [documentId, setDocumentId] = useState(null);

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const charCount = text.length;

  const handleSummarize = useCallback(async () => {
    if (loading) return;
    if (!isUrlMode && wordCount < MIN_WORDS) {
      setError(`Minimum ${MIN_WORDS} words required.`);
      return;
    }
    if (isUrlMode && !url.trim()) {
      setError("Please enter a valid URL.");
      return;
    }

    try {
      setError(null);
      setLoading(true);
      setHasSummary(false);
      setDocumentId(null);

      let textToSummarize = text;

      if (isUrlMode) {
        const doc = await ingestUrl(url.trim());
        textToSummarize = doc.cleaned_content;
        setText(textToSummarize); // Auto-fill the text area so they can read what was ingested
        setDocumentId(doc.id);
      }

      const result = await summarizeText(textToSummarize);
      setSummaryText(result.summary);
      setQuality(result.quality || "full");
      setHasSummary(true);
    } catch (err) {
      setError(err.message || "Failed to connect to backend.");
    } finally {
      setLoading(false);
    }
  }, [loading, isUrlMode, wordCount, text, url]);

  const reset = useCallback(() => {
    setHasSummary(false);
    setSummaryText("");
    setText("");
    setUrl("");
    setDocumentId(null);
    setError(null);
  }, []);

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
    isUrlMode,
    setIsUrlMode,
    url,
    setUrl,
    documentId,
    onSummarize: handleSummarize,
    reset,
  };
}
