import { useRef, useState } from "react";
import { MODES } from "../../../hooks/useSummarizer.js";

const MODE_ICONS = {
  paragraph: "¶", bullets: "•", key_sentences: "❝", abstract: "📄",
  tldr: "⚡", outline: "≡", executive: "▤",
};

const MODE_TOOLTIPS = {
  paragraph: "Flowing prose",
  bullets: "Concise points",
  key_sentences: "Direct quotes",
  abstract: "Academic style",
  tldr: "Ultra-brief",
  outline: "Hierarchical",
  executive: "Business ready",
};

export default function ModeSelector({ summaryMode, setSummaryMode, hasSummary }) {
  const [tiltMode, setTiltMode] = useState(null);
  const [modeTooltip, setModeTooltip] = useState(null);
  const [modeScrollFaded, setModeScrollFaded] = useState(true);
  const modeScrollRef = useRef(null);

  if (hasSummary) return null;

  function handleModeScroll() {
    const el = modeScrollRef.current;
    if (!el) return;
    const atEnd = el.scrollLeft + el.clientWidth >= el.scrollWidth - 2;
    setModeScrollFaded(!atEnd);
  }

  function handleModeSelect(mode) {
    setTiltMode(mode);
    setSummaryMode(mode);
    setTimeout(() => setTiltMode(null), 300);
  }

  return (
    <div className="anim-modes" style={{ padding: "12px 24px" }}>
      <p className="section-header">Summary Mode</p>
      <div
        ref={modeScrollRef}
        onScroll={handleModeScroll}
        className="mode-selector-wrap"
        style={{ position: "relative" }}
      >
        <div className="mode-selector">
          {MODES.map((m) => (
            <button
              key={m.value}
              onClick={() => handleModeSelect(m.value)}
              className={`mode-card ${summaryMode === m.value ? "active" : ""} ${tiltMode === m.value ? "tilt" : ""}`}
              onMouseEnter={() => setModeTooltip(m.value)}
              onMouseLeave={() => setModeTooltip(null)}
              aria-label={`${m.label}: ${MODE_TOOLTIPS[m.value]}`}
            >
              <span className="mode-icon">{MODE_ICONS[m.value] || m.icon}</span>
              <span className="mode-label">{m.label}</span>
              {modeTooltip === m.value && (
                <div className="tooltip visible" style={{ bottom: "calc(100% + 8px)", left: "50%", transform: "translateX(-50%)" }}>
                  {MODE_TOOLTIPS[m.value]}
                </div>
              )}
            </button>
          ))}
        </div>
        {modeScrollFaded && (
          <div className="mode-fade-mask" style={{
            position: "absolute", right: 0, top: 0, bottom: 0,
            width: 48,
            background: "linear-gradient(to right, transparent, var(--bg-surface))",
            pointerEvents: "none",
            zIndex: 2,
          }} />
        )}
      </div>
    </div>
  );
}
