/**
 * OutputCard — Summary output orchestrator.
 * Composes SummaryToolbar, SummaryContent, CompressionBar, and other panels.
 */
import { useState, useMemo, useCallback } from "react";
import SummaryToolbar from "./components/SummaryToolbar";
import SummaryContent from "./components/SummaryContent";
import CompressionBar from "./components/CompressionBar";
import ChatView from "./ChatView";
import DocumentActions from "./DocumentActions";
import KeyTakeaways from "./KeyTakeaways";
import KeyThemesGraph from "./KeyThemesGraph.jsx";
import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";

const MODE_LABELS = {
  paragraph: "Paragraph", bullets: "Bullet Points", key_sentences: "Key Sentences",
  abstract: "Abstract", tldr: "TL;DR", outline: "Outline", executive: "Executive Summary",
};

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

  const handleCopy = useCallback(async () => {
    try { await navigator.clipboard.writeText(summaryText); }
    catch {
      const ta = document.createElement("textarea");
      ta.value = summaryText; document.body.appendChild(ta);
      ta.select(); document.execCommand("copy"); document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }, [summaryText]);

  // Download with timestamp filename
  function handleDownload() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
    const blob = new Blob([summaryText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url;
    a.download = `probexr-summary-${timestamp}.txt`; a.click();
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
          <SummaryToolbar
            copied={copied}
            onCopy={handleCopy}
            onDownload={handleDownload}
            onSummarize={onSummarize}
            onReset={reset}
          />
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
        <SummaryContent
          showLoading={showLoading}
          showSummary={showSummary}
          summaryText={summaryText}
          streaming={streaming}
          isRestored={isRestored}
          streamingText={streamingText}
          summaryMode={summaryMode}
        />
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
    </div>
  );
}