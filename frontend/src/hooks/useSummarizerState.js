/**
 * useSummarizerState — form state, options, localStorage persistence, and loading UI.
 *
 * Owns all input/output/options state. Does NOT own streaming or history.
 */
import { useEffect, useState, useCallback, useRef } from "react";
import { config } from "../config.js";

const LOADING_MESSAGES = config.loadingMessages;

export function useSummarizerState() {
  // ── Input ──
  const [text, setText] = useState(() => localStorage.getItem("rp_text") || "");
  const [url, setUrl] = useState("");
  const [isUrlMode, setIsUrlMode] = useState(false);

  // ── Output ──
  const [summaryText, setSummaryText] = useState(() => localStorage.getItem("rp_summaryText") || "");
  const [hasSummary, setHasSummary] = useState(() => localStorage.getItem("rp_hasSummary") === "true");
  const [quality, setQuality] = useState("full");
  const [documentId, setDocumentId] = useState(() => {
    const saved = localStorage.getItem("rp_documentId");
    return saved ? parseInt(saved, 10) : null;
  });
  const [isRestored, setIsRestored] = useState(() => localStorage.getItem("rp_hasSummary") === "true");
  const [summaryMeta, setSummaryMeta] = useState(null);
  const [keyTakeaways, setKeyTakeaways] = useState(null);

  // ── Options ──
  const [summaryLength, setSummaryLength] = useState("standard");
  const [summaryMode, setSummaryMode] = useState("paragraph");
  const [summaryTone, setSummaryTone] = useState("neutral");
  const [focusKeywords, setFocusKeywords] = useState([]);
  const [focusArea, setFocusArea] = useState("");
  const [outputLanguage, setOutputLanguage] = useState("English");
  const [customInstructions, setCustomInstructions] = useState("");

  // ── UI / Loading ──
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState(null);
  const [summarizeStatus, setSummarizeStatus] = useState("idle");
  const textareaRef = useRef(null);

  // ── Derived ──
  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const charCount = text.length;
  const loadingMessage = LOADING_MESSAGES[loadingStep];

  // ── Reset advanced options ──
  const resetAdvanced = useCallback(() => {
    setFocusArea("");
    setOutputLanguage("English");
    setCustomInstructions("");
    setFocusKeywords([]);
    setSummaryTone("neutral");
  }, []);

  // ── Debounced localStorage persistence ──
  const persistTimer = useRef(null);
  useEffect(() => {
    clearTimeout(persistTimer.current);
    persistTimer.current = setTimeout(() => {
      localStorage.setItem("rp_text", text);
      localStorage.setItem("rp_hasSummary", hasSummary ? "true" : "false");
      localStorage.setItem("rp_summaryText", summaryText);
      if (documentId) {
        localStorage.setItem("rp_documentId", documentId.toString());
      } else {
        localStorage.removeItem("rp_documentId");
      }
    }, 300);
    return () => clearTimeout(persistTimer.current);
  }, [text, hasSummary, summaryText, documentId]);

  // ── Loading message rotation ──
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
    // Input
    text, setText,
    url, setUrl,
    isUrlMode, setIsUrlMode,
    wordCount, charCount,
    // Output
    summaryText, setSummaryText,
    hasSummary, setHasSummary,
    quality, setQuality,
    documentId, setDocumentId,
    isRestored, setIsRestored,
    summaryMeta, setSummaryMeta,
    keyTakeaways, setKeyTakeaways,
    // Options
    summaryLength, setSummaryLength,
    summaryMode, setSummaryMode,
    summaryTone, setSummaryTone,
    focusKeywords, setFocusKeywords,
    focusArea, setFocusArea,
    outputLanguage, setOutputLanguage,
    customInstructions, setCustomInstructions,
    resetAdvanced,
    // UI
    loading, setLoading,
    loadingMessage,
    error, setError,
    summarizeStatus, setSummarizeStatus,
    textareaRef,
  };
}
