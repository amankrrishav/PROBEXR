import { useEffect, useRef, useState, memo } from "react";

/**
 * TypingSummary — word-by-word reveal animation (ACT 4 of summarize ritual).
 * Three modes: streaming (SSE), instant (restored), word-stagger animation.
 */
const TypingSummary = memo(function TypingSummary({
  text = "",
  instant = false,
  streaming = false,
  streamingText = "",
  mode = "paragraph",
}) {
  const [displayedWords, setDisplayedWords] = useState([]);
  const [done, setDone] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }

    if (instant && text && !streaming) {
      setDisplayedWords(text.split(/(\s+)/));
      setDone(true);
      return;
    }

    setDisplayedWords([]);
    setDone(false);
    if (streaming || !text) return;

    const parts = text.split(/(\s+)/);
    let index = 0;
    intervalRef.current = setInterval(() => {
      if (index >= parts.length) {
        if (intervalRef.current) clearInterval(intervalRef.current);
        intervalRef.current = null;
        setDone(true);
        return;
      }
      index++;
      setDisplayedWords(parts.slice(0, index));
    }, 30);

    return () => { if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; } };
  }, [text, streaming, instant]);

  function handleShowFull() {
    if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
    setDisplayedWords(text.split(/(\s+)/));
    setDone(true);
  }

  // Mode-specific styles
  const modeStyles = {
    paragraph: { fontSize: 16, lineHeight: 1.8, fontFamily: "'Cabinet Grotesk', sans-serif" },
    bullets: { fontSize: 15, lineHeight: 1.7, fontFamily: "'Cabinet Grotesk', sans-serif" },
    key_sentences: { fontSize: 15, lineHeight: 1.7, fontFamily: "'Cabinet Grotesk', sans-serif" },
    abstract: { fontSize: 15, lineHeight: 1.8, fontFamily: "'Cabinet Grotesk', sans-serif" },
    tldr: { fontSize: 22, lineHeight: 1.5, fontFamily: "'Instrument Serif', Georgia, serif", fontStyle: "italic" },
    outline: { fontSize: 15, lineHeight: 1.7, fontFamily: "'Cabinet Grotesk', sans-serif" },
    executive: { fontSize: 15, lineHeight: 1.7, fontFamily: "'Cabinet Grotesk', sans-serif" },
  };

  const style = modeStyles[mode] || modeStyles.paragraph;

  // Streaming mode
  if (streaming) {
    return (
      <div style={{ ...style, color: "var(--ink-primary)", whiteSpace: "pre-line" }}>
        {streamingText || ""}
        <span style={{
          display: "inline-block", width: 5, height: 16,
          background: "var(--amber)", borderRadius: 1,
          animation: "amberPulseDot 1s infinite", marginLeft: 2,
          verticalAlign: "text-bottom",
        }} />
      </div>
    );
  }

  const isTyping = text?.length > 0 && !done;

  // Format bullets with amber squares
  const formatContent = (words) => {
    const fullText = words.join("");
    if (mode === "bullets") {
      return fullText.split('\n').map((line, i) => {
        const trimmed = line.replace(/^[-•*]\s*/, "");
        if (!trimmed) return <br key={i} />;
        if (line.match(/^[-•*]/)) {
          return (
            <div key={i} className="flex gap-3" style={{ marginBottom: 6 }}>
              <span style={{ color: "var(--amber)", fontSize: 8, marginTop: 7, flexShrink: 0 }}>■</span>
              <span>{trimmed}</span>
            </div>
          );
        }
        return <p key={i} style={{ margin: "0 0 8px" }}>{line}</p>;
      });
    }
    if (mode === "executive") {
      return fullText.split('\n').map((line, i) => {
        // Section headers (lines that look like labels)
        if (line.match(/^[A-Z][A-Z\s]+:/) || line.match(/^#+/)) {
          const cleanLine = line.replace(/^#+\s*/, "");
          return (
            <div key={i} className="font-mono" style={{
              fontSize: 11, textTransform: "uppercase", color: "var(--amber)",
              letterSpacing: "0.1em", marginTop: i > 0 ? 16 : 0, marginBottom: 6,
            }}>
              {cleanLine}
            </div>
          );
        }
        if (!line.trim()) return <br key={i} />;
        return <p key={i} style={{ margin: "0 0 8px" }}>{line}</p>;
      });
    }
    if (mode === "outline") {
      return fullText.split('\n').map((line, i) => {
        if (line.match(/^#+\s/) || line.match(/^[A-Z]/)) {
          const cleanLine = line.replace(/^#+\s*/, "");
          return (
            <h3 key={i} className="font-display" style={{
              fontSize: 18, color: "var(--ink-primary)",
              marginTop: i > 0 ? 16 : 0, marginBottom: 6,
            }}>
              {cleanLine}
            </h3>
          );
        }
        if (!line.trim()) return <br key={i} />;
        return <p key={i} style={{ margin: "0 0 6px", paddingLeft: 16 }}>{line}</p>;
      });
    }
    return fullText.split('\n').map((line, i) => (
      line.trim() ? <p key={i} style={{ margin: "0 0 8px" }}>{line}</p> : <br key={i} />
    ));
  };

  return (
    <div style={{ ...style, color: "var(--ink-primary)" }}>
      {displayedWords.length > 0 ? formatContent(displayedWords) : null}
      {isTyping && (
        <button
          type="button"
          onClick={handleShowFull}
          className="font-mono"
          style={{
            marginTop: 12, fontSize: 11, color: "var(--ink-tertiary)",
            background: "none", border: "none", cursor: "pointer",
            transition: "color var(--dur-fast) var(--ease)",
          }}
          onMouseEnter={(e) => e.target.style.color = "var(--ink-secondary)"}
          onMouseLeave={(e) => e.target.style.color = "var(--ink-tertiary)"}
        >
          Show full ↓
        </button>
      )}
    </div>
  );
});

export default TypingSummary;