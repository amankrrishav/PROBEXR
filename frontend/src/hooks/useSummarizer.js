/**
 * Summarizer feature state and logic — keeps App thin.
 * Phase 2B: Streaming support with automatic fallback.
 * Phase 3: Length selector, rich metadata, key takeaways.
 */
import { useEffect, useState, useCallback, useRef } from "react";
import { config } from "../config.js";
import { summarizeText, summarizeTextStream, ingestUrl, ingestText } from "../services/api.js";

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

  // Streaming state
  const [streaming, setStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const abortControllerRef = useRef(null);

  // Upgrade: Length selector
  const [summaryLength, setSummaryLength] = useState("standard");

  // Upgrade: Rich metadata (word counts, compression, reading time)
  const [summaryMeta, setSummaryMeta] = useState(null);

  // Upgrade: Key takeaways
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

      // Attempt streaming first
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

            // Parse rich metadata from done event
            if (metadata) {
              setSummaryMeta({
                original_word_count: metadata.original_word_count,
                summary_word_count: metadata.summary_word_count,
                compression_ratio: metadata.compression_ratio,
                reading_time_seconds: metadata.reading_time_seconds,
              });
              setQuality(metadata.quality || "full");
            }
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
        );

        if (streamSucceeded) return;
      } catch {
        // Stream fetch itself failed — fall through to non-streaming
      }

      // Fallback: non-streaming
      setStreaming(false);
      setStreamingText("");
      setHasSummary(false);
      setLoading(true);
      abortControllerRef.current = null;

      const result = await summarizeText(textToSummarize, summaryLength);
      setSummaryText(result.summary);
      setQuality(result.quality || "full");
      setHasSummary(true);
      setIsRestored(false);

      // Rich metadata from non-streaming response
      setSummaryMeta({
        original_word_count: result.original_word_count,
        summary_word_count: result.summary_word_count,
        compression_ratio: result.compression_ratio,
        reading_time_seconds: result.reading_time_seconds,
      });
      setKeyTakeaways(result.key_takeaways || []);

    } catch (err) {
      setError(err.message || "Failed to connect to backend.");
      setStreaming(false);
      setStreamingText("");
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, [loading, streaming, isUrlMode, wordCount, text, url, summaryLength]);

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
    // Streaming
    streaming,
    streamingText,
    cancelStreaming,
    // Upgrade: length
    summaryLength,
    setSummaryLength,
    // Upgrade: metadata
    summaryMeta,
    keyTakeaways,
    onSummarize: handleSummarize,
    reset,
  };
}
