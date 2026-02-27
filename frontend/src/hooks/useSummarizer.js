/**
 * Summarizer feature state and logic — keeps App thin. Add new feature hooks the same way.
 */
import { useEffect, useState, useCallback } from "react";
import { config } from "../config.js";
import { summarizeText, ingestUrl, ingestText } from "../services/api.js";

const MIN_WORDS = config.summarizer.minWords;
const LOADING_MESSAGES = config.loadingMessages;

export function useSummarizer() {
  const [text, setText] = useState(() => localStorage.getItem("rp_text") || "");
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState(null);
  const [hasSummary, setHasSummary] = useState(() => localStorage.getItem("rp_hasSummary") === "true");
  const [summaryText, setSummaryText] = useState(() => localStorage.getItem("rp_summaryText") || "");
  const [quality, setQuality] = useState("full");
  const [isUrlMode, setIsUrlMode] = useState(false);
  const [url, setUrl] = useState("");
  const [documentId, setDocumentId] = useState(() => {
    const saved = localStorage.getItem("rp_documentId");
    return saved ? parseInt(saved, 10) : null;
  });
  const [isRestored, setIsRestored] = useState(() => localStorage.getItem("rp_hasSummary") === "true");

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
      } else {
        try {
          const doc = await ingestText(textToSummarize);
          setDocumentId(doc.id);
        } catch (err) {
          // It's okay if this fails (e.g. unauthenticated). We just won't show advanced features.
          console.warn("Could not save document, advanced features disabled:", err.message);
        }
      }

      const result = await summarizeText(textToSummarize);
      setSummaryText(result.summary);
      setQuality(result.quality || "full");
      setHasSummary(true);
      setIsRestored(false);
    } catch (err) {
      setError(err.message || "Failed to connect to backend.");
    } finally {
      setLoading(false);
    }
  }, [loading, isUrlMode, wordCount, text, url]);

  // Sync state to localStorage to survive page refreshes
  useEffect(() => {
    localStorage.setItem("rp_text", text);
    localStorage.setItem("rp_hasSummary", hasSummary ? "true" : "false");
    localStorage.setItem("rp_summaryText", summaryText);
    if (documentId) {
      localStorage.setItem("rp_documentId", documentId.toString());
    } else {
      localStorage.removeItem("rp_documentId");
    }
  }, [text, hasSummary, summaryText, documentId]);

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
    isRestored,
    onSummarize: handleSummarize,
    reset,
  };
}
