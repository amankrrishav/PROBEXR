export default function InputTabs({
  hasSummary,
  isUrlMode,
  setIsUrlMode,
  text,
  setText,
  url,
  setUrl,
  isSampleLoaded,
  setIsSampleLoaded,
  handleLoadSample,
  handleClearSample,
  handleClear
}) {
  if (hasSummary) return null;

  const SAMPLE_TEXT = `Artificial intelligence has rapidly transformed from a research curiosity into a cornerstone of modern technology...`;

  return (
    <div className="flex items-center" style={{
      padding: "0 24px", borderBottom: "1px solid var(--border-dim)",
    }}>
      {["text", "url"].map((tab) => {
        const isActive = tab === "url" ? isUrlMode : !isUrlMode;
        return (
          <button
            key={tab}
            onClick={() => setIsUrlMode(tab === "url")}
            className="font-body"
            style={{
              padding: "14px 16px",
              fontSize: 13,
              fontWeight: 500,
              color: isActive ? "var(--ink-primary)" : "var(--ink-tertiary)",
              background: "none",
              border: "none",
              borderBottom: isActive ? "2px solid var(--amber)" : "2px solid transparent",
              cursor: "pointer",
              transition: "all var(--dur-fast) var(--ease)",
              textTransform: "capitalize",
            }}
          >
            {tab === "text" ? "Text" : "URL"}
          </button>
        );
      })}

      <div style={{ flex: 1 }} />

      {/* Load sample / Clear sample toggle */}
      {!isUrlMode && !text && (
        <button onClick={handleLoadSample} className="btn-ghost" style={{ fontSize: 12, color: "var(--amber)" }}>
          Load sample
        </button>
      )}
      {!isUrlMode && isSampleLoaded && (
        <button onClick={handleClearSample} className="btn-ghost" style={{ fontSize: 12, color: "var(--amber)" }}>
          Clear sample
        </button>
      )}
      {(text && !isSampleLoaded) || url ? (
        <button onClick={handleClear} className="btn-ghost" style={{ fontSize: 12 }}>
          Clear
        </button>
      ) : null}
    </div>
  );
}
