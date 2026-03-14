/**
 * Summarizer feature — composition hook.
 *
 * Composes three focused sub-hooks and wires the cross-cutting
 * handleSummarize / reset / restoreFromHistory logic.
 *
 * Public API is identical to the previous monolith so no consumer changes needed.
 */
import { useCallback } from "react";
import { config } from "../config.js";
import { summarizeText, summarizeTextStream, ingestUrl, ingestText } from "../services/api.js";
import { useSummarizerState } from "./useSummarizerState.js";
import { useStreaming } from "./useStreaming.js";
import { useSummaryHistory } from "./useSummaryHistory.js";

const MIN_WORDS = config.summarizer.minWords;

// ── Constants (re-exported for UI components) ──
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
  // ── Sub-hooks ──
  const state = useSummarizerState();
  const stream = useStreaming();
  const { history, addEntry } = useSummaryHistory();

  // ── Cancel streaming (flush partial text) ──
  const cancelStreaming = useCallback(() => {
    stream.cancelStreaming();
    state.setLoading(false);
    if (stream.streamingText) {
      state.setSummaryText(stream.streamingText);
      state.setHasSummary(true);
    }
  }, [stream, state]);

  // ── Add to history (bridge old shape → addEntry) ──
  const addToHistory = useCallback((entry) => {
    addEntry({
      inputText: entry.inputText,
      summaryText: entry.summaryText,
      mode: entry.mode,
      lengthSetting: entry.length,
      inputWordCount: entry.inputText ? entry.inputText.split(/\s+/).length : 0,
      timestamp: entry.timestamp,
    });
  }, [addEntry]);

  // ── Restore from history ──
  const restoreFromHistory = useCallback((entry) => {
    state.setSummaryText(entry.summaryText || "");
    state.setText(entry.inputText || "");
    state.setSummaryMeta(entry.meta || null);
    state.setKeyTakeaways(entry.takeaways || []);
    state.setSummaryMode(entry.mode || "paragraph");
    state.setSummaryLength(entry.lengthSetting || entry.length || "standard");
    state.setHasSummary(true);
    state.setIsRestored(true);
  }, [state]);

  // ── Main summarize action ──
  const handleSummarize = useCallback(async () => {
    if (state.loading || stream.streaming) return;
    if (!state.isUrlMode && state.wordCount < MIN_WORDS) {
      state.setError(`Minimum ${MIN_WORDS} words required.`);
      return;
    }
    if (state.isUrlMode && !state.url.trim()) {
      state.setError("Please enter a valid URL.");
      return;
    }
    if (state.isUrlMode) {
      try {
        new URL(state.url.trim());
      } catch {
        state.setError("Please enter a valid URL (e.g. https://example.com).");
        return;
      }
    }

    try {
      state.setError(null);
      state.setLoading(true);
      state.setHasSummary(false);
      state.setDocumentId(null);
      state.setSummaryText("");
      stream.setStreamingText("");
      state.setSummaryMeta(null);
      state.setKeyTakeaways(null);
      state.setSummarizeStatus("idle");

      let textToSummarize = state.text;

      if (state.isUrlMode) {
        const doc = await ingestUrl(state.url.trim());
        textToSummarize = doc.cleaned_content;
        state.setText(textToSummarize);
        state.setDocumentId(doc.id);
      } else {
        try {
          const doc = await ingestText(textToSummarize);
          state.setDocumentId(doc.id);
        } catch (err) {
          console.warn("Could not save document, advanced features disabled:", err.message);
        }
      }

      // Streaming first
      const controller = new AbortController();
      stream.abortControllerRef.current = controller;
      stream.setStreaming(true);
      state.setHasSummary(true);
      state.setLoading(false);

      let streamSucceeded = false;
      let streamedContent = "";

      try {
        await summarizeTextStream(
          textToSummarize,
          state.summaryLength,
          (token) => {
            streamedContent += token;
            stream.setStreamingText(streamedContent);
          },
          (metadata) => {
            streamSucceeded = true;
            state.setSummaryText(streamedContent);
            stream.setStreamingText("");
            stream.setStreaming(false);
            state.setIsRestored(false);
            stream.abortControllerRef.current = null;
            state.setSummarizeStatus("success");
            setTimeout(() => state.setSummarizeStatus("idle"), 600);

            if (metadata) {
              state.setSummaryMeta(metadata);
              state.setQuality(metadata.quality || "full");
            }

            addToHistory({
              summaryText: streamedContent,
              inputText: textToSummarize.slice(0, 200),
              meta: metadata,
              takeaways: null,
              mode: state.summaryMode,
              length: state.summaryLength,
              timestamp: new Date().toISOString(),
            });
          },
          (takeaways) => {
            if (Array.isArray(takeaways)) {
              state.setKeyTakeaways(takeaways);
            }
          },
          (errMsg) => {
            console.warn("Streaming failed, falling back:", errMsg);
          },
          controller,
          state.summaryMode,
          state.summaryTone,
          state.focusKeywords,
        );

        if (streamSucceeded) return;
      } catch {
        // Stream fetch failed — fall through to non-streaming
      }

      // Fallback: non-streaming
      stream.setStreaming(false);
      stream.setStreamingText("");
      state.setHasSummary(false);
      state.setLoading(true);
      stream.abortControllerRef.current = null;

      const result = await summarizeText(textToSummarize, state.summaryLength, state.summaryMode, state.summaryTone, state.focusKeywords);
      state.setSummaryText(result.summary);
      state.setQuality(result.quality || "full");
      state.setHasSummary(true);
      state.setIsRestored(false);
      state.setSummaryMeta(result);
      state.setKeyTakeaways(result.key_takeaways || []);
      state.setSummarizeStatus("success");
      setTimeout(() => state.setSummarizeStatus("idle"), 600);

      addToHistory({
        summaryText: result.summary,
        inputText: textToSummarize.slice(0, 200),
        meta: result,
        takeaways: result.key_takeaways || [],
        mode: state.summaryMode,
        length: state.summaryLength,
        timestamp: new Date().toISOString(),
      });

    } catch (err) {
      state.setError(err.message || "Failed to connect to backend.");
      stream.setStreaming(false);
      stream.setStreamingText("");
      state.setSummarizeStatus("error");
      setTimeout(() => state.setSummarizeStatus("idle"), 2000);
    } finally {
      state.setLoading(false);
      stream.abortControllerRef.current = null;
    }
  }, [state, stream, addToHistory]);

  // ── Full reset ──
  const reset = useCallback(() => {
    cancelStreaming();
    state.setHasSummary(false);
    state.setSummaryText("");
    stream.setStreamingText("");
    state.setText("");
    state.setUrl("");
    state.setDocumentId(null);
    state.setError(null);
    stream.setStreaming(false);
    state.setSummaryMeta(null);
    state.setKeyTakeaways(null);
    state.setSummaryMode("paragraph");
    state.setSummaryLength("standard");
    state.setFocusArea("");
    state.setOutputLanguage("English");
    state.setCustomInstructions("");
    state.setFocusKeywords([]);
    state.setSummaryTone("neutral");
    state.setIsUrlMode(false);
    state.setSummarizeStatus("idle");
    setTimeout(() => state.textareaRef.current?.focus(), 50);
  }, [cancelStreaming, state, stream]);

  // ── Return identical public API ──
  return {
    text: state.text, setText: state.setText,
    loading: state.loading,
    loadingMessage: state.loadingMessage,
    error: state.error, setError: state.setError,
    wordCount: state.wordCount, charCount: state.charCount,
    hasSummary: state.hasSummary, summaryText: state.summaryText, quality: state.quality,
    isUrlMode: state.isUrlMode, setIsUrlMode: state.setIsUrlMode,
    url: state.url, setUrl: state.setUrl,
    documentId: state.documentId,
    isRestored: state.isRestored,
    // Streaming
    streaming: stream.streaming, streamingText: stream.streamingText, cancelStreaming,
    // Mode, Tone, Keywords
    summaryLength: state.summaryLength, setSummaryLength: state.setSummaryLength,
    summaryMode: state.summaryMode, setSummaryMode: state.setSummaryMode,
    summaryTone: state.summaryTone, setSummaryTone: state.setSummaryTone,
    focusKeywords: state.focusKeywords, setFocusKeywords: state.setFocusKeywords,
    // History (in-memory)
    history, restoreFromHistory,
    // Metadata
    summaryMeta: state.summaryMeta, keyTakeaways: state.keyTakeaways,
    // Advanced options
    focusArea: state.focusArea, setFocusArea: state.setFocusArea,
    outputLanguage: state.outputLanguage, setOutputLanguage: state.setOutputLanguage,
    customInstructions: state.customInstructions, setCustomInstructions: state.setCustomInstructions,
    resetAdvanced: state.resetAdvanced,
    // Status flash
    summarizeStatus: state.summarizeStatus,
    // Textarea ref
    textareaRef: state.textareaRef,
    onSummarize: handleSummarize,
    reset,
  };
}
