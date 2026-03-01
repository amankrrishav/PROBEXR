import { useState } from "react";
import TypingSummary from "./TypingSummary";
import ChatView from "./ChatView";
import DocumentActions from "./DocumentActions";
import SummaryStats from "./SummaryStats";
import KeyTakeaways from "./KeyTakeaways";
import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";

export default function OutputCard() {
  const {
    summaryText,
    documentId,
    isRestored,
    streaming,
    streamingText,
    summaryMeta,
    keyTakeaways,
    reset,
  } = useSummarizerContext();

  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(summaryText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
      const ta = document.createElement("textarea");
      ta.value = summaryText;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  return (
    <div className="bg-white dark:bg-[#121212] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">

      {/* Header with actions */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xs uppercase tracking-wider text-gray-400">
          Summary
        </h3>
        {summaryText && !streaming && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="text-[11px] px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:text-black dark:hover:text-white transition"
            >
              {copied ? "✓ Copied" : "Copy"}
            </button>
            <button
              onClick={reset}
              className="text-[11px] px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:text-black dark:hover:text-white transition"
            >
              New Summary
            </button>
          </div>
        )}
      </div>

      {/* Summary stats — compression, word counts, reading time */}
      {!streaming && summaryMeta && (
        <SummaryStats meta={summaryMeta} />
      )}

      <TypingSummary
        text={summaryText}
        instant={isRestored}
        streaming={streaming}
        streamingText={streamingText}
      />

      {/* Key takeaways — appears after streaming */}
      {!streaming && keyTakeaways && keyTakeaways.length > 0 && (
        <KeyTakeaways takeaways={keyTakeaways} />
      )}

      {documentId && !streaming && (
        <>
          <DocumentActions documentId={documentId} />
          <ChatView documentId={documentId} />
        </>
      )}
    </div>
  );
}