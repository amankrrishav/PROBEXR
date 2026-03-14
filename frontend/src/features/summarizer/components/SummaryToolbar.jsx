/**
 * SummaryToolbar — Copy, download, regenerate, refine, and new-summary actions.
 */
import { useState, useEffect, useRef } from "react";

/* ── Refine Dropdown ── */
function RefineDropdown({ onRefine }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const close = (e) => { if (!ref.current?.contains(e.target)) setOpen(false); };
    document.addEventListener("click", close);
    return () => document.removeEventListener("click", close);
  }, [open]);

  const options = [
    "Make it shorter",
    "Simplify the language",
    "Make it more detailed",
    "Switch to Bullets",
    "Switch to TL;DR",
  ];

  return (
    <div ref={ref} className="relative" style={{ display: "inline-block" }}>
      <button
        onClick={() => setOpen(!open)}
        className="btn-ghost"
        style={{ fontSize: 12 }}
      >
        ✦ Refine ▾
      </button>
      {open && (
        <div style={{
          position: "absolute", top: "100%", right: 0, marginTop: 4,
          background: "var(--bg-overlay)", border: "1px solid var(--border-dim)",
          borderRadius: "var(--radius-btn)", padding: 4, zIndex: 50,
          boxShadow: "var(--shadow-lift)", minWidth: 200,
        }}>
          {options.map((opt, i) => (
            <button
              key={i}
              onClick={() => { onRefine?.(opt); setOpen(false); }}
              className="font-body w-full text-left"
              style={{
                display: "block", padding: "8px 12px",
                fontSize: 13, color: "var(--ink-secondary)",
                background: "none", border: "none", cursor: "pointer",
                borderRadius: 6,
                transition: "all var(--dur-fast) var(--ease)",
              }}
              onMouseEnter={(e) => {
                e.target.style.background = "var(--bg-elevated)";
                e.target.style.color = "var(--ink-primary)";
              }}
              onMouseLeave={(e) => {
                e.target.style.background = "none";
                e.target.style.color = "var(--ink-secondary)";
              }}
            >
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Summary Toolbar ── */
export default function SummaryToolbar({ copied, onCopy, onDownload, onSummarize, onReset }) {
  return (
    <div className="flex items-center gap-1">
      {/* Copy with checkmark icon */}
      <button onClick={onCopy} className="btn-ghost" style={{ fontSize: 12 }} aria-label="Copy summary">
        {copied ? "✓ Copied" : "📋 Copy"}
      </button>
      {/* Download with timestamp */}
      <button onClick={onDownload} className="btn-ghost" style={{ fontSize: 12 }} aria-label="Download summary">
        ⬇ Download
      </button>
      {/* Regenerate */}
      <button onClick={onSummarize} className="btn-ghost" style={{ fontSize: 12 }} aria-label="Regenerate summary">
        🔁 Regenerate
      </button>
      <RefineDropdown onRefine={() => {}} />
      <button onClick={onReset} className="btn-ghost" style={{ fontSize: 12 }} aria-label="New summary">
        ✦ New
      </button>
    </div>
  );
}
