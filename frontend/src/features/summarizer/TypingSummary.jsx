import { useEffect, useState } from "react";

export default function TypingSummary({ text }) {
  const [displayedText, setDisplayedText] = useState("");

  useEffect(() => {
    if (!text) return;

    setDisplayedText("");
    let index = 0;

    const interval = setInterval(() => {
      setDisplayedText((prev) => prev + text[index]);
      index++;

      if (index >= text.length) {
        clearInterval(interval);
      }
    }, 6);

    return () => clearInterval(interval);
  }, [text]);

  return (
    <p className="text-sm leading-relaxed whitespace-pre-line">
      {displayedText}
    </p>
  );
}