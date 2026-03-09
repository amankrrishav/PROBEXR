import { useState, useRef } from "react";
import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";
import { MODES, TONES } from "../../hooks/useSummarizer.js";

const LENGTH_OPTIONS = [
  { value: "brief", label: "Short" },
  { value: "standard", label: "Medium" },
  { value: "detailed", label: "Long" },
];

const MODE_ICONS = {
  paragraph: "¶", bullets: "•", key_sentences: "❝", abstract: "📄",
  tldr: "⚡", outline: "≡", executive: "📊",
};

const SAMPLE_TEXT = `Artificial intelligence has rapidly transformed from a research curiosity into a cornerstone of modern technology. In the past decade, advances in deep learning, natural language processing, and computer vision have enabled applications that were previously considered science fiction. Self-driving cars navigate complex urban environments, language models generate human-quality text, and AI systems diagnose diseases with accuracy rivaling experienced physicians.

However, this rapid advancement has also raised significant concerns. Issues of bias in training data, the environmental cost of training large models, and the potential for job displacement have sparked intense debate among policymakers, technologists, and the public. The concentration of AI capabilities in a small number of large technology companies has also raised questions about market power and democratic governance of transformative technologies.

Looking forward, the field faces critical decisions about safety, alignment, and regulation. Researchers are increasingly focused on developing AI systems that are not only capable but also trustworthy, transparent, and aligned with human values. The next decade will likely determine whether AI becomes a tool for broad human flourishing or a source of deepening inequality and existential risk.`;

export default function Editor({ onSummarize, handleKeyDown }) {
  const {
    text, setText, loading, loadingMessage, error, wordCount, charCount,
    hasSummary, isUrlMode, setIsUrlMode, url, setUrl,
    streaming, cancelStreaming, summaryLength, setSummaryLength,
    summaryMode, setSummaryMode, summaryTone, setSummaryTone,
    focusKeywords, setFocusKeywords,
  } = useSummarizerContext();

  const [keywordInput, setKeywordInput] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [textareaFocused, setTextareaFocused] = useState(false);
  const textareaRef = useRef(null);
  const isBusy = loading || streaming;
  const isMac = typeof navigator !== "undefined" && /Mac/i.test(navigator.userAgent);

  function handleAddKeyword(e) {
    if (e.key === "Enter" && keywordInput.trim() && focusKeywords.length < 5) {
      e.preventDefault();
      setFocusKeywords([...focusKeywords, keywordInput.trim()]);
      setKeywordInput("");
    }
  }

  function handleRemoveKeyword(idx) {
    setFocusKeywords(focusKeywords.filter((_, i) => i !== idx));
  }

  function handleLoadSample() {
    setText(SAMPLE_TEXT);
    setIsUrlMode(false);
  }

  function handleClear() {
    setText("");
    setUrl("");
  }

  const inputTabs = [
    { id: "text", label: "Text" },
    { id: "url", label: "URL" },
  ];

  return (
    <div>
      {/* ── Hero header (only before summary) ── */}
      {!hasSummary && (
        <div style={{ marginBottom: 32 }}>
          <h1 className="font-display" style={{ fontSize: 40, fontWeight: 800, color: "var(--text-primary)", lineHeight: 1.1 }}>
            Distill what matters.
          </h1>
          <p className="font-body" style={{ fontSize: 15, color: "var(--text-secondary)", marginTop: 8 }}>
            Drop in any text — get the essence in seconds.
          </p>
        </div>
      )}

      {/* ── Error ── */}
      {error && (
        <div className="flex items-center gap-2 animate-in" style={{
          padding: "12px 16px", borderRadius: "var(--radius-btn)", marginBottom: 16,
          background: "rgba(255,107,107,0.08)", border: "1px solid rgba(255,107,107,0.2)",
          fontSize: 13, color: "var(--accent-warn)",
        }}>
          <span>⚠</span> {error}
        </div>
      )}

      {/* ── Input Card ── */}
      <div className={`card ${textareaFocused ? "card-focused" : ""}`}>
        {/* Tab row */}
        {!hasSummary && (
          <div className="flex items-center gap-1" style={{ padding: "16px 20px 0" }}>
            <div className="segmented-control" style={{ width: "auto" }}>
              {inputTabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setIsUrlMode(tab.id === "url")}
                  className={(tab.id === "url" ? isUrlMode : !isUrlMode) ? "active" : ""}
                  style={{ padding: "6px 16px" }}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Sample text button */}
            {!isUrlMode && !text && (
              <button onClick={handleLoadSample} className="btn-ghost ml-auto" style={{ fontSize: 12, color: "var(--accent)" }}>
                Load sample
              </button>
            )}
            {text && (
              <button onClick={handleClear} className="btn-ghost ml-auto" style={{ fontSize: 12 }}>
                Clear
              </button>
            )}
          </div>
        )}

        {/* Input area */}
        <div style={{ padding: "16px 20px 12px" }}>
          {isUrlMode && !hasSummary ? (
            <div className="flex items-center gap-3">
              <span style={{ color: "var(--text-tertiary)", fontSize: 18 }}>🌐</span>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="https://example.com/article"
                className="font-body"
                style={{
                  flex: 1, background: "transparent", border: "none", outline: "none",
                  fontSize: 14, color: "var(--text-primary)",
                  padding: "8px 0",
                }}
                autoFocus
              />
            </div>
          ) : (
            <div className="relative">
              <textarea
                ref={textareaRef}
                rows={hasSummary ? 5 : 8}
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setTextareaFocused(true)}
                onBlur={() => setTextareaFocused(false)}
                placeholder={hasSummary ? "" : "Paste your article, paper, research, notes..."}
                readOnly={hasSummary && isUrlMode}
                className="font-mono"
                style={{
                  width: "100%", resize: "none", outline: "none",
                  fontSize: 13, lineHeight: 1.8,
                  background: "transparent", border: "none",
                  color: "var(--text-primary)",
                  minHeight: hasSummary ? 120 : 240,
                  maxHeight: "60vh",
                }}
              />
              {/* Word/char counter */}
              {text && (
                <span className="font-mono" style={{
                  position: "absolute", bottom: 4, right: 4,
                  fontSize: 11, color: "var(--text-tertiary)",
                }}>
                  {wordCount.toLocaleString()} words · {charCount.toLocaleString()} chars
                </span>
              )}
            </div>
          )}
        </div>

        {/* ── Mode Grid (only before summary) ── */}
        {!hasSummary && (
          <div style={{ padding: "0 20px 16px" }}>
            <p className="section-header">Summary Mode</p>
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: 8,
            }}>
              {MODES.map((m) => (
                <button
                  key={m.value}
                  onClick={() => setSummaryMode(m.value)}
                  className={`mode-card ${summaryMode === m.value ? "active" : ""}`}
                >
                  <span className="mode-icon">{MODE_ICONS[m.value] || m.icon}</span>
                  <span className="mode-label">{m.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── Advanced Options ── */}
        {!hasSummary && (
          <div style={{ padding: "0 20px 16px" }}>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="section-header flex items-center gap-2"
              style={{ cursor: "pointer", border: "none", background: "none", padding: 0 }}
            >
              <span style={{
                fontSize: 8, transition: "transform 200ms",
                transform: showAdvanced ? "rotate(90deg)" : "rotate(0deg)",
              }}>▸</span>
              Advanced Options
            </button>

            {showAdvanced && (
              <div className="animate-in" style={{ marginTop: 12 }}>
                <div className="flex gap-6 flex-wrap">
                  {/* Tone */}
                  <div style={{ flex: 1, minWidth: 200 }}>
                    <p className="section-header" style={{ marginBottom: 8 }}>Tone</p>
                    <div className="segmented-control">
                      {TONES.map((t) => (
                        <button
                          key={t.value}
                          onClick={() => setSummaryTone(t.value)}
                          className={summaryTone === t.value ? "active" : ""}
                        >
                          {t.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Keywords */}
                  <div style={{ flex: 1, minWidth: 200 }}>
                    <p className="section-header" style={{ marginBottom: 8 }}>
                      Focus Keywords ({focusKeywords.length}/5)
                    </p>
                    <div className="flex items-center gap-2 flex-wrap" style={{
                      padding: "8px 12px", borderRadius: "var(--radius-input)",
                      background: "var(--bg-input)", border: "1px solid var(--border)",
                      minHeight: 36,
                    }}>
                      {focusKeywords.map((kw, i) => (
                        <span key={i} className="chip chip-accent" style={{ gap: 6 }}>
                          {kw}
                          <button
                            onClick={() => handleRemoveKeyword(i)}
                            style={{
                              background: "none", border: "none", cursor: "pointer",
                              color: "var(--accent-warn)", fontSize: 12, padding: 0,
                            }}
                          >×</button>
                        </span>
                      ))}
                      {focusKeywords.length < 5 ? (
                        <input
                          type="text"
                          value={keywordInput}
                          onChange={(e) => setKeywordInput(e.target.value)}
                          onKeyDown={handleAddKeyword}
                          placeholder="Type + Enter"
                          className="font-mono"
                          style={{
                            background: "transparent", border: "none", outline: "none",
                            fontSize: 12, color: "var(--text-primary)", width: 100,
                          }}
                        />
                      ) : (
                        <span className="font-mono" style={{ fontSize: 11, color: "var(--text-tertiary)" }}>Max reached</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Bottom Action Bar ── */}
        <div className="flex items-center justify-between flex-wrap gap-3" style={{
          padding: "12px 20px",
          borderTop: "1px solid var(--border)",
        }}>
          {/* Left: word count + shortcut */}
          <div className="flex items-center gap-4">
            <span className="font-mono" style={{ fontSize: 12, color: "var(--text-tertiary)" }}>
              {wordCount.toLocaleString()} words
            </span>
            {!hasSummary && (
              <span className="font-mono" style={{ fontSize: 11, color: "var(--text-tertiary)", opacity: 0.5 }}>
                {isMac ? "⌘" : "Ctrl"}+Enter
              </span>
            )}
          </div>

          {/* Right: length + action buttons */}
          <div className="flex items-center gap-3">
            {/* Length selector */}
            {!hasSummary && (
              <div className="segmented-control">
                {LENGTH_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setSummaryLength(opt.value)}
                    className={summaryLength === opt.value ? "active" : ""}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}

            {/* Cancel */}
            {streaming && (
              <button onClick={cancelStreaming} className="btn-ghost" style={{ color: "var(--accent-warn)" }}>
                Stop
              </button>
            )}

            {/* Summarize */}
            <button
              onClick={onSummarize}
              disabled={isBusy}
              className="btn-primary"
              style={{
                height: 44, minWidth: 140,
                background: isBusy ? "var(--accent)" : "var(--gradient-hero)",
              }}
            >
              {loading ? (
                <>
                  <span style={{
                    width: 14, height: 14, border: "2px solid rgba(255,255,255,0.3)",
                    borderTopColor: "white", borderRadius: "50%",
                    animation: "spin 600ms linear infinite", display: "inline-block",
                  }} />
                  {loadingMessage}
                </>
              ) : streaming ? "Streaming…" : (
                <>Summarize <span style={{ fontSize: 16 }}>→</span></>
              )}
            </button>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        input::placeholder, textarea::placeholder {
          color: var(--text-tertiary);
        }
      `}</style>
    </div>
  );
}