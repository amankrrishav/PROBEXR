import { useEffect, useRef, useState, memo } from "react";

/**
 * TypingSummary — renders summary text with three modes:
 *   1. streaming=true  → render streamingText directly (real-time SSE tokens)
 *   2. instant=true    → show full text immediately (restored from localStorage)
 *   3. fallback        → 50ms word-chunk animation (non-streaming path)
 *
 * All hooks run unconditionally to satisfy React Rules of Hooks.
 */
const TypingSummary = memo(function TypingSummary({
  text = "",
  instant = false,
  streaming = false,
  streamingText = "",
}) {
  const [displayedText, setDisplayedText] = useState("");
  const intervalRef = useRef(null);

  // Word-chunk animation — runs only when NOT streaming and NOT instant
  useEffect(() => {
    // Clean up any running animation
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // Skip animation during streaming or when there's no text
    if (streaming || !text) {
      setDisplayedText("");
      return;
    }

    if (instant) {
      setDisplayedText(text);
      return;
    }

    // Animate word-by-word (fallback for non-streaming)
    setDisplayedText("");
    const words = text.split(/(\s+)/); // split but keep whitespace
    let index = 0;
    let accumulated = "";

    intervalRef.current = setInterval(() => {
      if (index >= words.length) {
        if (intervalRef.current) clearInterval(intervalRef.current);
        intervalRef.current = null;
        return;
      }

      accumulated += words[index];
      index++;
      setDisplayedText(accumulated);
    }, 50);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [text, streaming, instant]);

  function handleShowFull() {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setDisplayedText(text);
  }

  // Mode 1: Real-time streaming — render streamingText directly with cursor
  if (streaming) {
    return (
      <div>
        <p className="text-[15px] leading-7 text-gray-700 dark:text-gray-300 whitespace-pre-line">
          {streamingText || ""}
          <span className="inline-block w-1.5 h-4 bg-gray-400 dark:bg-gray-500 animate-pulse ml-0.5 align-text-bottom" />
        </p>
      </div>
    );
  }

  // Mode 2 & 3: instant or animated (word-chunk fallback)
  const hasText = text && text.length > 0;
  const isTyping = hasText && displayedText.length < text.length;

  return (
    <div>
      <p className="text-[15px] leading-7 text-gray-700 dark:text-gray-300 whitespace-pre-line">
        {displayedText}
      </p>
      {isTyping && (
        <button
          type="button"
          onClick={handleShowFull}
          className="mt-4 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 underline"
        >
          Show full
        </button>
      )}
    </div>
  );
});

export default TypingSummary;