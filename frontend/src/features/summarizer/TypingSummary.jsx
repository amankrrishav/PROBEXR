import { useEffect, useRef, useState, memo } from "react";

/**
 * TypingSummary — renders summary text with three modes:
 *   1. streaming=true  → real-time SSE tokens with cursor
 *   2. instant=true    → show full text (restored from localStorage)
 *   3. fallback        → word-chunk animation
 */
const TypingSummary = memo(function TypingSummary({
  text = "",
  instant = false,
  streaming = false,
  streamingText = "",
}) {
  const [displayedText, setDisplayedText] = useState("");
  const intervalRef = useRef(null);

  useEffect(() => {
    if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
    
    if (instant && text && !streaming) { 
        setDisplayedText(text); 
        return; 
    }

    setDisplayedText("");
    if (streaming || !text) return;
    const words = text.split(/(\s+)/);
    let index = 0, accumulated = "";
    intervalRef.current = setInterval(() => {
      if (index >= words.length) {
        if (intervalRef.current) clearInterval(intervalRef.current);
        intervalRef.current = null;
        return;
      }
      accumulated += words[index];
      index++;
      setDisplayedText(accumulated);
    }, 40);

    return () => { if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; } };
  }, [text, streaming, instant]);

  function handleShowFull() {
    if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
    setDisplayedText(text);
  }

  // Streaming mode
  if (streaming) {
    return (
      <div>
        <p className="text-[14px] leading-[1.8] text-gray-700 dark:text-gray-300 whitespace-pre-line">
          {streamingText || ""}
          <span className="inline-block w-[5px] h-[16px] bg-gray-400 dark:bg-gray-500 animate-pulse ml-0.5 align-text-bottom rounded-sm" />
        </p>
      </div>
    );
  }

  const hasText = text?.length > 0;
  const isTyping = hasText && displayedText.length < text.length;

  return (
    <div>
      <p className="text-[14px] leading-[1.8] text-gray-700 dark:text-gray-300 whitespace-pre-line">
        {displayedText}
      </p>
      {isTyping && (
        <button
          type="button"
          onClick={handleShowFull}
          className="mt-3 text-[11px] text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
        >
          Show full ↓
        </button>
      )}
    </div>
  );
});

export default TypingSummary;