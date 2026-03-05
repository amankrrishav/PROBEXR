import { useState } from "react";
import TypingSummary from "./TypingSummary";
import ChatView from "./ChatView";
import DocumentActions from "./DocumentActions";
import SummaryStats from "./SummaryStats";
import KeyTakeaways from "./KeyTakeaways";
import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";

function NotableQuotes({ quotes }) {
  const [expanded, setExpanded] = useState(false);

  if (!quotes || quotes.length === 0) return null;

  return (
    <div className="border-t border-gray-100 dark:border-gray-800/60 pt-4 mt-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition w-full text-left mb-3"
      >
        <span className={`transition-transform duration-200 text-[10px] ${expanded ? "rotate-90" : ""}`}>
          ▸
        </span>
        Notable Quotes
        <span className="font-normal text-gray-300 dark:text-gray-600">{quotes.length}</span>
      </button>

      <div className={`overflow-hidden transition-all duration-300 ${expanded ? "max-h-[400px] opacity-100" : "max-h-0 opacity-0"}`}>
        <div className="space-y-3">
          {quotes.map((q, i) => (
            <blockquote
              key={i}
              className="border-l-2 border-gray-200 dark:border-gray-700 pl-4 text-[13px] leading-relaxed text-gray-500 dark:text-gray-400 italic"
            >
              "{q}"
            </blockquote>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function OutputCard() {
  const {
    summaryText, documentId, isRestored,
    streaming, streamingText, summaryMeta, keyTakeaways, reset,
  } = useSummarizerContext();

  const [copied, setCopied] = useState(false);

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

  const notableQuotes = summaryMeta?.notable_quotes;

  return (
    <div className="rounded-2xl border border-gray-200/80 dark:border-gray-800/80 bg-white dark:bg-[#111] overflow-hidden">

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-6 pt-5 pb-0">
        <h3 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500">
          Summary
        </h3>
        {summaryText && !streaming && (
          <div className="flex items-center gap-1">
            <button
              onClick={handleCopy}
              className="text-[11px] font-medium px-2.5 py-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-50 dark:hover:text-gray-300 dark:hover:bg-white/[0.03] transition"
            >
              {copied ? "Copied ✓" : "Copy"}
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

      {/* ── Stats ── */}
      {!streaming && summaryMeta && (
        <div className="px-6 pt-3">
          <SummaryStats meta={summaryMeta} />
        </div>
      )}

      {/* ── Summary text ── */}
      <div className="px-6 py-4">
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