import { useState, useMemo } from "react";
import TypingSummary from "./TypingSummary";
import ChatView from "./ChatView";
import DocumentActions from "./DocumentActions";
import SummaryStats from "./SummaryStats";
import KeyTakeaways from "./KeyTakeaways";
import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";

function EntitySection({ entities }) {
  if (!entities || (!entities.people?.length && !entities.orgs?.length && !entities.concepts?.length)) return null;

  return (
    <div className="border-t border-gray-100 dark:border-gray-800/60 pt-4 mt-2">
      <h4 className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">
        Intelligence Discovery
      </h4>
      <div className="flex flex-wrap gap-2">
        {entities.people?.map((p, i) => (
          <span key={`p-${i}`} className="text-[11px] px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-blue-800/50">
            👤 {p}
          </span>
        ))}
        {entities.orgs?.map((o, i) => (
          <span key={`o-${i}`} className="text-[11px] px-2 py-0.5 rounded-full bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 border border-purple-100 dark:border-purple-800/50">
            🏢 {o}
          </span>
        ))}
        {entities.concepts?.map((c, i) => (
          <span key={`c-${i}`} className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-800/50">
            💡 {c}
          </span>
        ))}
      </div>
    </div>
  );
}

function NotableQuotes({ quotes }) {
  const [expanded, setExpanded] = useState(false);
  if (!quotes || quotes.length === 0) return null;

  return (
    <div className="border-t border-gray-100 dark:border-gray-800/60 pt-4 mt-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition w-full text-left mb-3"
      >
        <span className={`transition-transform duration-200 text-[10px] ${expanded ? "rotate-90" : ""}`}>▸</span>
        Notable Quotes
        <span className="font-normal text-gray-300 dark:text-gray-600">{quotes.length}</span>
      </button>
      <div className={`overflow-hidden transition-all duration-300 ${expanded ? "max-h-[400px] opacity-100" : "max-h-0 opacity-0"}`}>
        <div className="space-y-3">
          {quotes.map((q, i) => (
            <blockquote key={i} className="border-l-2 border-gray-200 dark:border-gray-700 pl-4 text-[13px] leading-relaxed text-gray-500 dark:text-gray-400 italic">
              &quot;{q}&quot;
            </blockquote>
          ))}
        </div>
      </div>
    </div>
  );
}

function ModeLabel({ mode }) {
  const labels = {
    paragraph: "Paragraph",
    bullets: "Bullet Points",
    key_sentences: "Key Sentences",
    abstract: "Abstract",
    tldr: "TL;DR",
    outline: "Outline",
    executive: "Executive Summary",
  };
  return (
    <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-teal-50 dark:bg-teal-900/20 text-teal-600 dark:text-teal-400 border border-teal-200/50 dark:border-teal-700/50">
      {labels[mode] || mode}
    </span>
  );
}

export default function OutputCard() {
  const {
    summaryText, documentId, isRestored,
    streaming, streamingText, summaryMeta, keyTakeaways, reset,
    summaryMode,
  } = useSummarizerContext();

  const [copied, setCopied] = useState(false);
  const [showCompare, setShowCompare] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(summaryText);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = summaryText;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownload() {
    const blob = new Blob([summaryText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "summary.txt";
    a.click();
    URL.revokeObjectURL(url);
  }

  const notableQuotes = summaryMeta?.notable_quotes;

  // Compute stats
  const summaryWordCount = useMemo(() => summaryText?.trim().split(/\s+/).filter(Boolean).length || 0, [summaryText]);
  const compressionRatio = summaryMeta?.compression_ratio;
  const readingTime = summaryMeta?.reading_time_seconds;
  const originalWordCount = summaryMeta?.original_word_count;

  return (
    <div className="rounded-2xl border border-gray-200/80 dark:border-gray-800/80 bg-white dark:bg-[#111] overflow-hidden">

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-6 pt-5 pb-0 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <h3 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500">
            Summary
          </h3>
          {!streaming && summaryText && (
            <ModeLabel mode={summaryMode || "paragraph"} />
          )}
        </div>
        {summaryText && !streaming && (
          <div className="flex items-center gap-1">
            <button
              onClick={handleCopy}
              className="text-[11px] font-medium px-2.5 py-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-50 dark:hover:text-gray-300 dark:hover:bg-white/[0.03] transition"
            >
              {copied ? "Copied ✓" : "Copy"}
            </button>
            <button
              onClick={handleDownload}
              className="text-[11px] font-medium px-2.5 py-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-50 dark:hover:text-gray-300 dark:hover:bg-white/[0.03] transition"
            >
              Download
            </button>
            <button
              onClick={reset}
              className="text-[11px] font-medium px-2.5 py-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-50 dark:hover:text-gray-300 dark:hover:bg-white/[0.03] transition"
            >
              New
            </button>
          </div>
        )}
      </div>

      {/* ── Quick Stats Badges ── */}
      {!streaming && summaryText && (
        <div className="flex items-center gap-2 px-6 pt-3 flex-wrap">
          <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400">
            {summaryWordCount} words
          </span>
          {compressionRatio != null && (
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400">
              {compressionRatio.toFixed(0)}% compressed
            </span>
          )}
          {readingTime != null && (
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400">
              {readingTime < 60 ? `${readingTime}s read` : `${Math.ceil(readingTime / 60)}min read`}
            </span>
          )}
          {originalWordCount != null && (
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-gray-50 dark:bg-gray-800/50 text-gray-400 dark:text-gray-500">
              from {originalWordCount.toLocaleString()} words
            </span>
          )}
        </div>
      )}

      {/* ── Stats Panel ── */}
      {!streaming && summaryMeta && (
        <div className="px-6 pt-3">
          <SummaryStats meta={summaryMeta} />
        </div>
      )}

      {/* ── TL;DR ── */}
      {!streaming && summaryMeta?.tldr && (
        <div className="px-6 pt-3">
          <div className="p-3 rounded-xl bg-gray-50 dark:bg-white/[0.02] border border-gray-100 dark:border-white/[0.05]">
            <p className="text-[13px] font-medium leading-relaxed text-gray-700 dark:text-gray-300">
              <span className="text-[10px] uppercase tracking-wider text-teal-500 mr-2">TL;DR</span>
              {summaryMeta.tldr}
            </p>
          </div>
        </div>
      )}

      {/* ── Summary text ── */}
      <div className="px-6 py-4">
        {!summaryText && !streaming && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="text-4xl mb-3 opacity-20">📝</div>
            <p className="text-[13px] text-gray-400 dark:text-gray-500">Your summary will appear here</p>
          </div>
        )}
        <TypingSummary
          text={summaryText}
          instant={isRestored}
          streaming={streaming}
          streamingText={streamingText}
        />
      </div>

      {/* ── Takeaways ── */}
      {!streaming && keyTakeaways?.length > 0 && (
        <div className="px-6 pb-2">
          <KeyTakeaways takeaways={keyTakeaways} />
        </div>
      )}

      {/* ── Entities ── */}
      {!streaming && summaryMeta?.entities && (
        <div className="px-6 pb-2">
          <EntitySection entities={summaryMeta.entities} />
        </div>
      )}

      {/* ── Notable Quotes ── */}
      {!streaming && notableQuotes?.length > 0 && (
        <div className="px-6 pb-2">
          <NotableQuotes quotes={notableQuotes} />
        </div>
      )}

      {/* ── Actions + Chat ── */}
      {documentId && !streaming && (
        <div className="px-6 pb-6">
          <DocumentActions documentId={documentId} />
          <ChatView documentId={documentId} />
        </div>
      )}
    </div>
  );
}