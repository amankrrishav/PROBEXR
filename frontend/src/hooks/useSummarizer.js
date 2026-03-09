/**
 * Summarizer feature state and logic.
 * v2: Mode (7 formats), Tone (5 styles), Keywords, History (last 5).
 * Clean streaming — no JSON separator filtering needed.
 */
import { useEffect, useState, useCallback, useRef } from "react";
import { config } from "../config.js";
import { summarizeText, summarizeTextStream, ingestUrl, ingestText } from "../services/api.js";

const MIN_WORDS = config.summarizer.minWords;
const LOADING_MESSAGES = config.loadingMessages;

const MODES = [
  { value: "paragraph", label: "Paragraph", icon: "¶" },
  { value: "bullets", label: "Bullets", icon: "•" },
  { value: "key_sentences", label: "Key Sentences", icon: "❝" },
  { value: "abstract", label: "Abstract", icon: "📄" },
  { value: "tldr", label: "TL;DR", icon: "⚡" },
  { value: "outline", label: "Outline", icon: "≡" },
  { value: "executive", label: "Executive", icon: "📊" },
];

const TONES = [
  { value: "neutral", label: "Neutral" },
  { value: "formal", label: "Formal" },
  { value: "casual", label: "Simple" },
  { value: "creative", label: "Creative" },
  { value: "technical", label: "Technical" },
];

export { MODES, TONES };

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

  // Streaming state
  const [streaming, setStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const abortControllerRef = useRef(null);

  // v2: Mode, Tone, Keywords, History
  const [summaryLength, setSummaryLength] = useState("standard");
  const [summaryMode, setSummaryMode] = useState("paragraph");
  const [summaryTone, setSummaryTone] = useState("neutral");
  const [focusKeywords, setFocusKeywords] = useState([]);
  const [history, setHistory] = useState([]);
  const [summaryMeta, setSummaryMeta] = useState(null);
  const [keyTakeaways, setKeyTakeaways] = useState(null);

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const charCount = text.length;

  const cancelStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStreaming(false);
    setLoading(false);
    if (streamingText) {
      setSummaryText(streamingText);
      setHasSummary(true);
    }
  }, [streamingText]);

  // Add to history
  const addToHistory = useCallback((entry) => {
    setHistory(prev => {
      const next = [entry, ...prev].slice(0, 5);
      return next;
    });
  }, []);

  // Restore from history
  const restoreFromHistory = useCallback((entry) => {
    setSummaryText(entry.summaryText);
    setText(entry.inputText || "");
    setSummaryMeta(entry.meta || null);
    setKeyTakeaways(entry.takeaways || []);
    setSummaryMode(entry.mode || "paragraph");
    setSummaryLength(entry.length || "standard");
    setHasSummary(true);
    setIsRestored(true);
  }, []);

  const handleSummarize = useCallback(async () => {
    if (loading || streaming) return;
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
      setSummaryText("");
      setStreamingText("");
      setSummaryMeta(null);
      setKeyTakeaways(null);

      let textToSummarize = text;

      if (isUrlMode) {
        const doc = await ingestUrl(url.trim());
        textToSummarize = doc.cleaned_content;
        setText(textToSummarize);
        setDocumentId(doc.id);
      } else {
        try {
          const doc = await ingestText(textToSummarize);
          setDocumentId(doc.id);
        } catch (err) {
          console.warn("Could not save document, advanced features disabled:", err.message);
        }
      }

      // Streaming first
      const controller = new AbortController();
      abortControllerRef.current = controller;
      setStreaming(true);
      setHasSummary(true);
      setLoading(false);

      let streamSucceeded = false;
      let streamedContent = "";

      try {
        await summarizeTextStream(
          textToSummarize,
          summaryLength,
          // onToken
          (token) => {
            streamedContent += token;
            setStreamingText(streamedContent);
          },
          // onDone
          (metadata) => {
            streamSucceeded = true;
            setSummaryText(streamedContent);
            setStreamingText("");
            setStreaming(false);
            setIsRestored(false);
            abortControllerRef.current = null;

            if (metadata) {
              setSummaryMeta(metadata);
              setQuality(metadata.quality || "full");
            }

            // Add to history
            addToHistory({
              summaryText: streamedContent,
              inputText: textToSummarize.slice(0, 200),
              meta: metadata,
              takeaways: null, // will be set separately
              mode: summaryMode,
              length: summaryLength,
              timestamp: new Date().toISOString(),
            });
          },
          // onTakeaways
          (takeaways) => {
            if (Array.isArray(takeaways)) {
              setKeyTakeaways(takeaways);
            }
          },
          // onError
          (errMsg) => {
            console.warn("Streaming failed, falling back:", errMsg);
          },
          controller,
          summaryMode,
          summaryTone,
          focusKeywords,
        );

        if (streamSucceeded) return;
      } catch {
        // Stream fetch failed — fall through to non-streaming
      }

      // Fallback: non-streaming
      setStreaming(false);
      setStreamingText("");
      setHasSummary(false);
      setLoading(true);
      abortControllerRef.current = null;

      const result = await summarizeText(textToSummarize, summaryLength, summaryMode, summaryTone, focusKeywords);
      setSummaryText(result.summary);
      setQuality(result.quality || "full");
      setHasSummary(true);
      setIsRestored(false);
      setSummaryMeta(result);
      setKeyTakeaways(result.key_takeaways || []);

      addToHistory({
        summaryText: result.summary,
        inputText: textToSummarize.slice(0, 200),
        meta: result,
        takeaways: result.key_takeaways || [],
        mode: summaryMode,
        length: summaryLength,
        timestamp: new Date().toISOString(),
      });

    } catch (err) {
      setError(err.message || "Failed to connect to backend.");
      setStreaming(false);
      setStreamingText("");
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, [loading, streaming, isUrlMode, wordCount, text, url, summaryLength, summaryMode, summaryTone, focusKeywords, addToHistory]);

  // Sync state to localStorage
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
    cancelStreaming();
    setHasSummary(false);
    setSummaryText("");
    setStreamingText("");
    setText("");
    setUrl("");
    setDocumentId(null);
    setError(null);
    setStreaming(false);
    setSummaryMeta(null);
    setKeyTakeaways(null);
  }, [cancelStreaming]);

  // Rotate loading message
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
    text, setText,
    loading,
    loadingMessage: LOADING_MESSAGES[loadingStep],
    error,
    wordCount, charCount,
    hasSummary, summaryText, quality,
    isUrlMode, setIsUrlMode,
    url, setUrl,
    documentId,
    isRestored,
    // Streaming
    streaming, streamingText, cancelStreaming,
    // v2: Mode, Tone, Keywords
    summaryLength, setSummaryLength,
    summaryMode, setSummaryMode,
    summaryTone, setSummaryTone,
    focusKeywords, setFocusKeywords,
    // v2: History
    history, restoreFromHistory,
    // Metadata
    summaryMeta, keyTakeaways,
    onSummarize: handleSummarize,
    reset,
  };
}
