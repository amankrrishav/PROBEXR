import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";

const MODE_LABELS = {
  paragraph: "Paragraph", bullets: "Bullets", key_sentences: "Key Sentences",
  abstract: "Abstract", tldr: "TL;DR", outline: "Outline", executive: "Executive",
};

export default function SummaryHistory() {
  const { history, restoreFromHistory } = useSummarizerContext();

  if (!history || history.length === 0) return null;

  return (
    <div className="card" style={{ overflow: "hidden" }}>
      <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border-dim)" }}>
        <p className="section-header" style={{ margin: 0, padding: 0 }}>Recent Summaries</p>
      </div>
      <div>
        {history.map((entry, i) => {
          const time = entry.timestamp
            ? new Date(entry.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
            : "";
          const preview = entry.inputText
            ? (entry.inputText.length > 55 ? entry.inputText.slice(0, 55) + "…" : entry.inputText)
            : "—";
          const mode = MODE_LABELS[entry.mode] || entry.mode;

          return (
            <button
              key={i}
              onClick={() => restoreFromHistory(entry)}
              className="w-full text-left flex items-center gap-3"
              style={{
                padding: "12px 20px",
                borderBottom: i < history.length - 1 ? "1px solid var(--border-dim)" : "none",
                background: "transparent",
                transition: "all var(--dur-fast) var(--ease)",
                border: "none", cursor: "pointer",
                color: "var(--ink-primary)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "var(--bg-elevated)";
                e.currentTarget.style.paddingLeft = "24px";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "transparent";
                e.currentTarget.style.paddingLeft = "20px";
              }}
            >
              <span style={{ color: "var(--ink-tertiary)", fontSize: 14 }}>○</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p className="truncate font-body" style={{ fontSize: 12, color: "var(--ink-secondary)", margin: 0 }}>
                  {preview}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="chip chip-amber" style={{ fontSize: 10 }}>{mode}</span>
                <span className="font-mono" style={{ fontSize: 10, color: "var(--ink-tertiary)" }}>{time}</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
