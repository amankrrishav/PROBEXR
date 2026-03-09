import { useState, useMemo } from "react";
import TypingSummary from "./TypingSummary";
import ChatView from "./ChatView";
import DocumentActions from "./DocumentActions";
import KeyTakeaways from "./KeyTakeaways";
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

function CompressionBar({ originalWords, summaryWords }) {
  if (!originalWords || !summaryWords) return null;
  const ratio = Math.round((summaryWords / originalWords) * 100);

  return (
    <div style={{ marginTop: 16 }}>
      <p className="section-header" style={{ marginBottom: 12 }}>Compression</p>
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-3">
          <span className="font-mono" style={{ fontSize: 11, color: "var(--text-tertiary)", width: 56, textAlign: "right" }}>
            Original
          </span>
          <div className="compression-bar flex-1">
            <div className="fill" style={{ width: "100%", background: "var(--border-active)" }} />
          </div>
          <span className="font-mono" style={{ fontSize: 11, color: "var(--text-secondary)", width: 56 }}>
            {originalWords.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-mono" style={{ fontSize: 11, color: "var(--text-tertiary)", width: 56, textAlign: "right" }}>
            Summary
          </span>
          <div className="compression-bar flex-1">
            <div className="fill" style={{ width: `${ratio}%`, background: "var(--accent)" }} />
          </div>
          <span className="font-mono" style={{ fontSize: 11, color: "var(--accent)", width: 56 }}>
            {summaryWords.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
}

function LoadingState() {
  const [phase, setPhase] = useState(0);

  useState(() => {
    const interval = setInterval(() => {
      setPhase((p) => (p + 1) % LOADING_PHASES.length);
    }, 1500);
    return () => clearInterval(interval);
  });

  return (
    <div className="animate-in">
      {/* Progress bar */}
      <div style={{
        height: 2, background: "var(--bg-elevated)", borderRadius: 1,
        overflow: "hidden", marginBottom: 32,
      }}>
        <div style={{
          height: "100%", background: "var(--accent)", borderRadius: 1,
          width: "75%", animation: "progressPulse 2s ease-in-out infinite",
        }} />
      </div>

      {/* Skeleton lines */}
      <div className="flex flex-col gap-3" style={{ marginBottom: 24 }}>
        <div className="skeleton" style={{ height: 14, width: "100%" }} />
        <div className="skeleton" style={{ height: 14, width: "95%" }} />
        <div className="skeleton" style={{ height: 14, width: "100%" }} />
        <div className="skeleton" style={{ height: 14, width: "60%" }} />
      </div>

      {/* Phase text */}
      <p className="font-body" style={{ fontSize: 13, color: "var(--text-secondary)", textAlign: "center" }}>
        {LOADING_PHASES[phase]}
      </p>

      <style>{`
        @keyframes progressPulse {
          0%, 100% { opacity: 1; width: 65%; }
          50% { opacity: 0.7; width: 80%; }
        }
      `}</style>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center text-center" style={{ padding: "64px 32px" }}>
      {/* Overlapping doc icon */}
      <div style={{ position: "relative", width: 72, height: 72, marginBottom: 24 }}>
        <div style={{
          position: "absolute", top: 0, left: 8,
          width: 48, height: 56, borderRadius: 8,
          border: "2px solid var(--border)", background: "var(--bg-elevated)",
        }} />
        <div style={{
          position: "absolute", top: 8, left: 16,
          width: 48, height: 56, borderRadius: 8,
          border: "2px solid var(--border-active)", background: "var(--bg-surface)",
        }}>
          <div style={{ padding: "12px 8px", display: "flex", flexDirection: "column", gap: 4 }}>
            <div style={{ height: 3, borderRadius: 1, background: "var(--border)", width: "80%" }} />
            <div style={{ height: 3, borderRadius: 1, background: "var(--border)", width: "100%" }} />
            <div style={{ height: 3, borderRadius: 1, background: "var(--border)", width: "60%" }} />
          </div>
        </div>
      </div>

      <h3 className="font-body" style={{ fontSize: 15, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>
        Your summary will appear here
      </h3>
      <p className="font-body" style={{ fontSize: 13, color: "var(--text-tertiary)", maxWidth: 260 }}>
        Paste text on the left and hit Summarize to distill it instantly.
      </p>
    </div>
  );
}

export default function OutputCard() {
  const {
    summaryText, documentId, isRestored, loading,
    streaming, streamingText, summaryMeta, keyTakeaways, reset,
    summaryMode, hasSummary, onSummarize,
  } = useSummarizerContext();

  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try { await navigator.clipboard.writeText(summaryText); }
    catch {
      const ta = document.createElement("textarea");
      ta.value = summaryText; document.body.appendChild(ta);
      ta.select(); document.execCommand("copy"); document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownload() {
    const blob = new Blob([summaryText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url;
    a.download = "summary.txt"; a.click();
    URL.revokeObjectURL(url);
  }

  const summaryWordCount = useMemo(() => summaryText?.trim().split(/\s+/).filter(Boolean).length || 0, [summaryText]);
  const compressionRatio = summaryMeta?.compression_ratio;
  const readingTime = summaryMeta?.reading_time_seconds;
  const originalWordCount = summaryMeta?.original_word_count;

  // Compute time saved (assuming 200 wpm reading speed)
  const timeSaved = originalWordCount ? Math.max(0, Math.round(((originalWordCount - summaryWordCount) / 200) * 60)) : null;

  const showSummary = summaryText && !streaming && !loading;
  const showStreaming = streaming || (summaryText && streaming);
  const showLoading = loading && !streaming && !summaryText;

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
            <button onClick={reset} className="btn-ghost" style={{ fontSize: 12 }}>
              ✦ New
            </button>
          </div>
        )}
      </div>

      {/* ── Metadata chips ── */}
      {showSummary && (
        <div className="flex items-center gap-2 flex-wrap" style={{ padding: "12px 24px 0" }}>
          <span className="chip chip-accent">{MODE_LABELS[summaryMode] || summaryMode}</span>
          <span className="chip">{summaryWordCount} words</span>
          {compressionRatio != null && (
            <span className="chip chip-teal">Compressed to {(100 - compressionRatio).toFixed(0)}%</span>
          )}
          {timeSaved != null && timeSaved > 0 && (
            <span className="chip">
              Saved {timeSaved >= 60 ? `${Math.floor(timeSaved / 60)}min ${timeSaved % 60}sec` : `${timeSaved}sec`}
            </span>
          )}
        </div>
      )}

      {/* ── Summary Content ── */}
      <div style={{ padding: "16px 24px 20px" }}>
        {showLoading ? (
          <LoadingState />
        ) : !summaryText && !streaming ? (
          <EmptyState />
        ) : (
          <div className="font-body" style={{
            fontSize: 15, lineHeight: 1.7, color: "var(--text-primary)",
          }}>
            <TypingSummary
              text={summaryText}
              instant={isRestored}
              streaming={streaming}
              streamingText={streamingText}
            />
          </div>
        )}
      </div>

      {/* ── Takeaways ── */}
      {showSummary && keyTakeaways?.length > 0 && (
        <div style={{ padding: "0 24px 16px" }}>
          <KeyTakeaways takeaways={keyTakeaways} />
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
    </div>
  );
}