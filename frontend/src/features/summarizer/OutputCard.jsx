import { useState, useMemo, useEffect, useRef, useCallback } from "react";
import TypingSummary from "./TypingSummary";
import ChatView from "./ChatView";
import DocumentActions from "./DocumentActions";
import KeyTakeaways from "./KeyTakeaways";
import KeyThemesGraph from "./KeyThemesGraph.jsx";
import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";

const MODE_LABELS = {
  paragraph: "Paragraph", bullets: "Bullet Points", key_sentences: "Key Sentences",
  abstract: "Abstract", tldr: "TL;DR", outline: "Outline", executive: "Executive Summary",
};

const LOADING_PHASES = [
  "Reading your document...",
  "Identifying key arguments...",
  "Structuring your summary...",
  "Polishing output...",
];

/* ── Animated Counter ── */
function useAnimatedValue(target, duration = 800) {
  const [value, setValue] = useState(0);
  const raf = useRef(null);
  useEffect(() => {
    if (!target) { setValue(0); return; }
    const start = performance.now();
    function tick(now) {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(Math.round(target * eased));
      if (t < 1) raf.current = requestAnimationFrame(tick);
    }
    raf.current = requestAnimationFrame(tick);
    return () => raf.current && cancelAnimationFrame(raf.current);
  }, [target, duration]);
  return value;
}

/* ── Compression Bar ── */
function CompressionBar({ originalWords, summaryWords }) {
  if (!originalWords || !summaryWords) return null;
  const ratio = Math.round((summaryWords / originalWords) * 100);
  const [animReady, setAnimReady] = useState(false);
  const animOriginal = useAnimatedValue(animReady ? originalWords : 0);
  const animSummary = useAnimatedValue(animReady ? summaryWords : 0);

  useEffect(() => {
    const t = setTimeout(() => setAnimReady(true), 100);
    return () => clearTimeout(t);
  }, []);

  return (
    <div style={{ marginTop: 16 }}>
      <p className="section-header" style={{ marginBottom: 12 }}>Compression</p>
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-3">
          <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-tertiary)", width: 56, textAlign: "right" }}>
            Original
          </span>
          <div className="compression-bar" style={{ flex: 1 }}>
            <div className="fill" style={{
              width: animReady ? "100%" : "0%",
              background: "var(--border-lit)",
            }} />
          </div>
          <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-secondary)", width: 56 }}>
            {animOriginal.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-tertiary)", width: 56, textAlign: "right" }}>
            Summary
          </span>
          <div className="compression-bar" style={{ flex: 1 }}>
            <div className="fill" style={{
              width: animReady ? `${ratio}%` : "0%",
              background: "var(--amber)",
              boxShadow: "var(--glow-amber)",
            }} />
          </div>
          <span className="font-mono" style={{ fontSize: 11, color: "var(--amber)", width: 56 }}>
            {animSummary.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
}

/* ── Loading State ── */
function LoadingState() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setPhase((p) => (p + 1) % LOADING_PHASES.length);
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="animate-in">
      <div style={{
        height: 2, background: "var(--bg-elevated)", borderRadius: 1,
        overflow: "hidden", marginBottom: 32,
      }}>
        <div style={{
          height: "100%", background: "var(--amber)", borderRadius: 1,
          animation: "progressGrow 3s ease-in-out infinite",
        }} />
      </div>

      <div className="flex flex-col gap-3" style={{ marginBottom: 24 }}>
        <div className="skeleton" style={{ height: 14, width: "100%" }} />
        <div className="skeleton" style={{ height: 14, width: "95%" }} />
        <div className="skeleton" style={{ height: 14, width: "100%" }} />
        <div className="skeleton" style={{ height: 14, width: "60%" }} />
      </div>

      <p className="font-mono" style={{ fontSize: 12, color: "var(--ink-tertiary)", textAlign: "center" }}>
        {LOADING_PHASES[phase]}
      </p>
    </div>
  );
}

/* ── Empty State ── */
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center text-center" style={{ padding: "64px 32px" }}>
      <div style={{ position: "relative", width: 72, height: 72, marginBottom: 24 }}>
        <div style={{
          position: "absolute", top: 0, left: 8,
          width: 48, height: 56, borderRadius: 8,
          border: "2px solid var(--border-dim)", background: "var(--bg-elevated)",
        }} />
        <div style={{
          position: "absolute", top: 8, left: 16,
          width: 48, height: 56, borderRadius: 8,
          border: "2px solid var(--border-lit)", background: "var(--bg-surface)",
        }}>
          <div style={{ padding: "12px 8px", display: "flex", flexDirection: "column", gap: 4 }}>
            <div style={{ height: 3, borderRadius: 1, background: "var(--border-dim)", width: "80%" }} />
            <div style={{ height: 3, borderRadius: 1, background: "var(--border-dim)", width: "100%" }} />
            <div style={{ height: 3, borderRadius: 1, background: "var(--border-dim)", width: "60%" }} />
          </div>
        </div>
      </div>

      <h3 className="font-body" style={{ fontSize: 15, fontWeight: 600, color: "var(--ink-secondary)", marginBottom: 6 }}>
        Your summary will appear here
      </h3>
      <p className="font-body" style={{ fontSize: 13, color: "var(--ink-tertiary)", maxWidth: 260 }}>
        Paste text above and hit Summarize to distill it instantly.
      </p>
    </div>
  );
}

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


/* ═══════════════════════════════════════════════════════════════
   OUTPUT CARD — THE PAYOFF
   ═══════════════════════════════════════════════════════════════ */
export default function OutputCard() {
  const {
    summaryText, documentId, isRestored, loading,
    streaming, streamingText, summaryMeta, keyTakeaways, reset,
    summaryMode, hasSummary, onSummarize,
  } = useSummarizerContext();

  const [copied, setCopied] = useState(false);
  const [showCopyToast, setShowCopyToast] = useState(false);

  const handleCopy = useCallback(async () => {
    try { await navigator.clipboard.writeText(summaryText); }
    catch {
      const ta = document.createElement("textarea");
      ta.value = summaryText; document.body.appendChild(ta);
      ta.select(); document.execCommand("copy"); document.body.removeChild(ta);
    }
    setCopied(true);
    setShowCopyToast(true);
    setTimeout(() => setCopied(false), 2000);
    setTimeout(() => setShowCopyToast(false), 2500);
  }, [summaryText]);

  function handleDownload() {
    const blob = new Blob([summaryText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url;
    a.download = "summary.txt"; a.click();
    URL.revokeObjectURL(url);
  }

  const summaryWordCount = useMemo(() => summaryText?.trim().split(/\s+/).filter(Boolean).length || 0, [summaryText]);
  const compressionRatio = summaryMeta?.compression_ratio;
  const originalWordCount = summaryMeta?.original_word_count;

  // Compute reading time & time saved
  const readingTimeSec = Math.round(summaryWordCount / 200 * 60);
  const originalReadingTimeSec = originalWordCount ? Math.round(originalWordCount / 200 * 60) : null;
  const timeSaved = originalWordCount ? Math.max(0, Math.round(((originalWordCount - summaryWordCount) / 200) * 60)) : null;

  const formatTime = (s) => {
    if (s < 60) return `${s} sec`;
    return `${Math.floor(s / 60)} min`;
  };

  const showSummary = summaryText && !streaming && !loading;
  const showStreaming = streaming || (summaryText && streaming);
  const showLoading = loading && !streaming && !summaryText;

  // Extract simple themes from key takeaways for the graph
  const themes = useMemo(() => {
    if (!keyTakeaways?.length) return [];
    return keyTakeaways.slice(0, 8).map(t => {
      // Extract key phrase (first few words)
      const words = t.split(/\s+/).slice(0, 3).join(" ");
      return words;
    });
  }, [keyTakeaways]);

  return (
    <div className="card" style={{ overflow: "hidden" }}>
      {/* ── Header ── */}
      <div className="flex items-center justify-between flex-wrap gap-2" style={{ padding: "20px 24px 0" }}>
        <h3 className="section-header" style={{ padding: 0, margin: 0 }}>Summary</h3>
        {showSummary && (
          <div className="flex items-center gap-1">
            <button onClick={handleCopy} className="btn-ghost" style={{ fontSize: 12 }}>
              {copied ? "✓ Copied!" : "📋 Copy"}
            </button>
            <button onClick={handleDownload} className="btn-ghost" style={{ fontSize: 12 }}>
              ⬇ Download
            </button>
            <button onClick={onSummarize} className="btn-ghost" style={{ fontSize: 12 }}>
              🔁 Regenerate
            </button>
            <RefineDropdown onRefine={() => {}} />
            <button onClick={reset} className="btn-ghost" style={{ fontSize: 12 }}>
              ✦ New
            </button>
          </div>
        )}
      </div>

      {/* ── Metadata chips ── */}
      {showSummary && (
        <div style={{ padding: "12px 24px 0" }}>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="chip chip-amber">{MODE_LABELS[summaryMode] || summaryMode}</span>
            <span className="chip">{summaryWordCount} words</span>
            {compressionRatio != null && (
              <span className="chip chip-sage">Compressed to {(100 - compressionRatio).toFixed(0)}%</span>
            )}
          </div>
          {/* Stats row */}
          <div className="font-mono flex items-center gap-3" style={{
            fontSize: 12, color: "var(--ink-secondary)",
            marginTop: 10, paddingBottom: 12,
            borderBottom: "1px solid var(--border-dim)",
          }}>
            <span>⏱ {formatTime(readingTimeSec)} read</span>
            {originalReadingTimeSec && (
              <span style={{ color: "var(--ink-tertiary)" }}>vs {formatTime(originalReadingTimeSec)} original</span>
            )}
            {timeSaved != null && timeSaved > 0 && (
              <span style={{ color: "var(--sage)" }}>
                Saved you ~{formatTime(timeSaved)}
              </span>
            )}
          </div>
        </div>
      )}

      {/* ── Summary Content ── */}
      <div style={{ padding: "16px 24px 20px" }}>
        {showLoading ? (
          <LoadingState />
        ) : !summaryText && !streaming ? (
          <EmptyState />
        ) : (
          <TypingSummary
            text={summaryText}
            instant={isRestored}
            streaming={streaming}
            streamingText={streamingText}
            mode={summaryMode}
          />
        )}
      </div>

      {/* ── Takeaways ── */}
      {showSummary && keyTakeaways?.length > 0 && (
        <div style={{ padding: "0 24px 16px" }}>
          <KeyTakeaways takeaways={keyTakeaways} />
        </div>
      )}

      {/* ── Key Themes Graph ── */}
      {showSummary && themes.length > 0 && (
        <div style={{ padding: "0 24px 16px" }}>
          <KeyThemesGraph themes={themes} />
        </div>
      )}

      {/* ── Compression Bar ── */}
      {showSummary && originalWordCount && (
        <div style={{ padding: "0 24px 20px" }}>
          <CompressionBar originalWords={originalWordCount} summaryWords={summaryWordCount} />
        </div>
      )}

      {/* ── Actions + Chat ── */}
      {documentId && showSummary && (
        <div style={{ padding: "0 24px 24px" }}>
          <DocumentActions documentId={documentId} />
          <ChatView documentId={documentId} />
        </div>
      )}

      {/* Copy Toast */}
      {showCopyToast && (
        <div className="toast">Copied to clipboard</div>
      )}
    </div>
  );
}