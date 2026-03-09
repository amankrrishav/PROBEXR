import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";

const MODE_LABELS = {
  paragraph: "Paragraph",
  bullets: "Bullets",
  key_sentences: "Key Sentences",
  abstract: "Abstract",
  tldr: "TL;DR",
  outline: "Outline",
  executive: "Executive",
};

export default function SummaryHistory() {
  const { history, restoreFromHistory } = useSummarizerContext();

  if (!history || history.length === 0) return null;

  return (
    <div className="rounded-2xl border border-gray-200/80 dark:border-gray-800/80 bg-white dark:bg-[#111] overflow-hidden">
      <div className="px-5 py-3 border-b border-gray-100 dark:border-gray-800/60">
        <h4 className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500">
          Recent Summaries
        </h4>
      </div>
      <div className="divide-y divide-gray-100 dark:divide-gray-800/60">
        {history.map((entry, i) => {
          const time = entry.timestamp
            ? new Date(entry.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
            : "";
          const preview = entry.inputText
            ? (entry.inputText.length > 60 ? entry.inputText.slice(0, 60) + "…" : entry.inputText)
            : "—";
          const mode = MODE_LABELS[entry.mode] || entry.mode;
          const length = entry.length || "standard";

          return (
            <button
              key={i}
              onClick={() => restoreFromHistory(entry)}
              className="w-full text-left px-5 py-3 hover:bg-gray-50 dark:hover:bg-white/[0.02] transition group"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-[11px] text-gray-400 dark:text-gray-500 tabular-nums">{time}</span>
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-teal-50 dark:bg-teal-900/20 text-teal-600 dark:text-teal-400">
                    {mode}
                  </span>
                  <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 capitalize">
                    {length}
                  </span>
                </div>
              </div>
              <p className="text-[12px] text-gray-500 dark:text-gray-400 truncate group-hover:text-gray-700 dark:group-hover:text-gray-300 transition">
                {preview}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
