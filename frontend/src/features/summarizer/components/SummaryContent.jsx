/**
 * SummaryContent — Renders summary as markdown, loading skeleton, or empty state.
 */
import { useState, useEffect } from "react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import TypingSummary from "../TypingSummary";

const LOADING_PHASES = [
  "Reading your document...",
  "Identifying key arguments...",
  "Structuring your summary...",
  "Polishing output...",
];

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

/* ── Summary Content ── */
export default function SummaryContent({
  showLoading, showSummary, summaryText, streaming,
  isRestored, streamingText, summaryMode,
}) {
  if (showLoading) {
    return <LoadingState />;
  }

  if (!summaryText && !streaming) {
    return <EmptyState />;
  }

  if (showSummary) {
    return (
      <div className="font-body markdown-body" style={{
        fontSize: 15, lineHeight: 1.75, color: "var(--ink-primary)",
        userSelect: "text",
      }}>
        <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>{summaryText}</ReactMarkdown>
      </div>
    );
  }

  return (
    <TypingSummary
      text={summaryText}
      instant={isRestored}
      streaming={streaming}
      streamingText={streamingText}
      mode={summaryMode}
    />
  );
}
