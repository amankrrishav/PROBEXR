import { useEffect, useRef, useState, memo } from "react";

const TypingSummary = memo(function TypingSummary({ text, instant = false }) {
  const [displayedText, setDisplayedText] = useState("");
  const [showFull, setShowFull] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!text) return;

    if (instant) {
      setDisplayedText(text);
      setShowFull(true);
      return;
    }

    setDisplayedText("");
    setShowFull(false);

    const words = text.split(/(\s+)/); // split but keep whitespace
    let index = 0;

    intervalRef.current = setInterval(() => {
      if (index >= words.length) {
        if (intervalRef.current) clearInterval(intervalRef.current);
        return;
      }

      setDisplayedText((prev) => prev + words[index]);
      index++;
    }, 50);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [text]);

  function handleShowFull() {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setDisplayedText(text);
    setShowFull(true);
  }

  const isTyping = text && displayedText.length < text.length;

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