/**
 * Summarizer feature state and logic.
 * v3: Mode (7 formats), Tone (5 styles), Keywords, Advanced Options,
 * localStorage-persisted history, length→prompt mapping.
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

const LENGTH_PROMPTS = {
  brief: "Respond in 2–3 sentences maximum.",
  standard: "Respond in a single well-structured paragraph.",
  detailed: "Respond in 3–5 detailed paragraphs.",
};

const LANGUAGES = ["English", "Spanish", "French", "Hindi", "Japanese"];

export { MODES, TONES, LENGTH_PROMPTS, LANGUAGES };

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

  // Mode, Tone, Keywords
  const [summaryLength, setSummaryLength] = useState("standard");
  const [summaryMode, setSummaryMode] = useState("paragraph");
  const [summaryTone, setSummaryTone] = useState("neutral");
  const [focusKeywords, setFocusKeywords] = useState([]);
  const [history, setHistory] = useState([]);
  const [summaryMeta, setSummaryMeta] = useState(null);
  const [keyTakeaways, setKeyTakeaways] = useState(null);

  // Advanced options (B10)
  const [focusArea, setFocusArea] = useState("");
  const [outputLanguage, setOutputLanguage] = useState("English");
  const [customInstructions, setCustomInstructions] = useState("");

  // Success/error flash states (C1)
  const [summarizeStatus, setSummarizeStatus] = useState("idle"); // 'idle' | 'success' | 'error'

  // Textarea ref for focus (B11)
  const textareaRef = useRef(null);

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

  // Add to in-memory history
  const addToHistory = useCallback((entry) => {
    setHistory(prev => {
      const next = [entry, ...prev].slice(0, 5);
      return next;
    });
  }, []);

  // Restore from history
  const restoreFromHistory = useCallback((entry) => {
    setSummaryText(entry.summaryText || "");
    setText(entry.inputText || "");
    setSummaryMeta(entry.meta || null);
    setKeyTakeaways(entry.takeaways || []);
    setSummaryMode(entry.mode || "paragraph");
    setSummaryLength(entry.length || entry.lengthSetting || "standard");
    setHasSummary(true);
    setIsRestored(true);
  }, []);

  // Reset advanced options
  const resetAdvanced = useCallback(() => {
    setFocusArea("");
    setOutputLanguage("English");
    setCustomInstructions("");
    setFocusKeywords([]);
    setSummaryTone("neutral");
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
    if (isUrlMode) {
      try {
        new URL(url.trim());
      } catch {
        setError("Please enter a valid URL (e.g. https://example.com).");
        return;
      }
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
      setSummarizeStatus("idle");

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
            setSummarizeStatus("success");
            setTimeout(() => setSummarizeStatus("idle"), 600);

            if (metadata) {
              setSummaryMeta(metadata);
              setQuality(metadata.quality || "full");
            }

            // Add to in-memory history
            addToHistory({
              summaryText: streamedContent,
              inputText: textToSummarize.slice(0, 200),
              meta: metadata,
              takeaways: null,
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
      setSummarizeStatus("success");
      setTimeout(() => setSummarizeStatus("idle"), 600);

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
      setSummarizeStatus("error");
      setTimeout(() => setSummarizeStatus("idle"), 2000);
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

  // B11: Full reset
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
    setSummaryMode("paragraph");
    setSummaryLength("standard");
    setFocusArea("");
    setOutputLanguage("English");
    setCustomInstructions("");
    setFocusKeywords([]);
    setSummaryTone("neutral");
    setIsUrlMode(false);
    setSummarizeStatus("idle");
    // Focus textarea after react renders
    setTimeout(() => textareaRef.current?.focus(), 50);
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
    error, setError,
    wordCount, charCount,
    hasSummary, summaryText, quality,
    isUrlMode, setIsUrlMode,
    url, setUrl,
    documentId,
    isRestored,
    // Streaming
    streaming, streamingText, cancelStreaming,
    // Mode, Tone, Keywords
    summaryLength, setSummaryLength,
    summaryMode, setSummaryMode,
    summaryTone, setSummaryTone,
    focusKeywords, setFocusKeywords,
    // History (in-memory)
    history, restoreFromHistory,
    // Metadata
    summaryMeta, keyTakeaways,
    // Advanced options (B10)
    focusArea, setFocusArea,
    outputLanguage, setOutputLanguage,
    customInstructions, setCustomInstructions,
    resetAdvanced,
    // Status flash (C1)
    summarizeStatus,
    // Textarea ref (B11)
    textareaRef,
    onSummarize: handleSummarize,
    reset,
  };
}
