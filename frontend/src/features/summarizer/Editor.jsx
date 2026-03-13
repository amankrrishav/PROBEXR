import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";
import { MODES, TONES } from "../../hooks/useSummarizer.js";

const LENGTH_OPTIONS = [
  { value: "brief", label: "Short" },
  { value: "standard", label: "Medium" },
  { value: "detailed", label: "Long" },
];

const MODE_ICONS = {
  paragraph: "¶", bullets: "•", key_sentences: "❝", abstract: "📄",
  tldr: "⚡", outline: "≡", executive: "▤",
};

const MODE_TOOLTIPS = {
  paragraph: "Flowing prose",
  bullets: "Concise points",
  key_sentences: "Direct quotes",
  abstract: "Academic style",
  tldr: "Ultra-brief",
  outline: "Hierarchical",
  executive: "Business ready",
};

const SAMPLE_TEXT = `Artificial intelligence has rapidly transformed from a research curiosity into a cornerstone of modern technology. In the past decade, advances in deep learning, natural language processing, and computer vision have enabled applications that were previously considered science fiction. Self-driving cars navigate complex urban environments, language models generate human-quality text, and AI systems diagnose diseases with accuracy rivaling experienced physicians.

However, this rapid advancement has also raised significant concerns. Issues of bias in training data, the environmental cost of training large models, and the potential for job displacement have sparked intense debate among policymakers, technologists, and the public. The concentration of AI capabilities in a small number of large technology companies has also raised questions about market power and democratic governance of transformative technologies.

Looking forward, the field faces critical decisions about safety, alignment, and regulation. Researchers are increasingly focused on developing AI systems that are not only capable but also trustworthy, transparent, and aligned with human values. The next decade will likely determine whether AI becomes a tool for broad human flourishing or a source of deepening inequality and existential risk.`;

/* ── Intelligence Score Calculation (pure JS heuristic) ── */
function getIntelligenceScore(text) {
  if (!text || text.trim().split(/\s+/).length < 50) return null;
  const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
  const words = text.trim().split(/\s+/);
  const avgWordLen = words.reduce((s, w) => s + w.length, 0) / words.length;
  const avgSentLen = words.length / Math.max(sentences.length, 1);

  if (avgWordLen > 6.5 || avgSentLen > 28) return { level: "academic", color: "var(--sky)", label: "Expert-level content", pos: 90 };
  if (avgWordLen > 5.5 || avgSentLen > 22) return { level: "complex", color: "var(--terra)", label: "Advanced readers", pos: 70 };
  if (avgWordLen > 4.5 || avgSentLen > 16) return { level: "moderate", color: "var(--amber)", label: "General audience", pos: 45 };
  return { level: "simple", color: "var(--sage)", label: "Readable by most", pos: 15 };
}

/* ── Word Count Color ── */
function getWordCountColor(count) {
  if (count === 0) return "var(--ink-tertiary)";
  if (count <= 50) return "var(--amber)";
  if (count <= 500) return "var(--sage)";
  return "var(--ink-secondary)";
}

export default function Editor({ onSummarize, handleKeyDown, focusMode }) {
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
  const [prevWordCount, setPrevWordCount] = useState(0);
  const [tiltMode, setTiltMode] = useState(null);
  const [loadingPhase, setLoadingPhase] = useState(0);
  const [modeTooltip, setModeTooltip] = useState(null);
  const textareaRef = useRef(null);
  const isBusy = loading || streaming;
  const isMac = typeof navigator !== "undefined" && /Mac/i.test(navigator.userAgent);

  const LOADING_PHASES = ["Reading...", "Extracting...", "Structuring...", "Refining..."];

  // Rotate loading phases
  useEffect(() => {
    if (!isBusy) return;
    setLoadingPhase(0);
    let i = 0;
    const interval = setInterval(() => {
      i = (i + 1) % LOADING_PHASES.length;
      setLoadingPhase(i);
    }, 1500);
    return () => clearInterval(interval);
  }, [isBusy]);

  // Track word count changes for flip animation
  useEffect(() => {
    setPrevWordCount(wordCount);
  }, [wordCount]);

  // Auto-grow textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, window.innerHeight * 0.6) + "px";
  }, [text]);

  const intelligenceScore = useMemo(() => getIntelligenceScore(text), [text]);

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

  function handleModeSelect(mode) {
    setTiltMode(mode);
    setSummaryMode(mode);
    setTimeout(() => setTiltMode(null), 300);
  }

  // Compute the active tone segment index for the sliding pill
  const toneIndex = TONES.findIndex(t => t.value === summaryTone);

  return (
    <div>
      {/* ── Hero header (only before summary) ── */}
      {!hasSummary && (
        <div className="anim-header" style={{ marginBottom: 32 }}>
          <h1 className="font-display" style={{
            fontSize: 48, color: "var(--ink-primary)", lineHeight: 1.1,
            fontWeight: 400, fontStyle: "normal",
          }}>
            Distill what matters.
          </h1>
          <p className="font-body" style={{ fontSize: 15, color: "var(--ink-secondary)", marginTop: 10 }}>
            Drop in any text — get the essence in seconds.
          </p>
        </div>
      )}

      {/* ── Error ── */}
      {error && (
        <div className="flex items-center gap-2 animate-in" style={{
          padding: "12px 16px", borderRadius: "var(--radius-btn)", marginBottom: 16,
          background: "rgba(224,92,92,0.08)", border: "1px solid rgba(224,92,92,0.2)",
          fontSize: 13, color: "var(--rose)",
        }}>
          <span>⚠</span> {error}
        </div>
      )}

      {/* ── Input Card ── */}
      <div
        className={`card anim-input ${textareaFocused ? "card-focused" : ""}`}
        style={{ position: "relative", overflow: "hidden" }}
      >
        {/* Progress line during loading */}
        {isBusy && <div className="progress-line" />}

        {/* Tab row */}
        {!hasSummary && (
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

            {!isUrlMode && !text && (
              <button onClick={handleLoadSample} className="btn-ghost" style={{ fontSize: 12, color: "var(--amber)" }}>
                Load sample
              </button>
            )}
            {(text || url) && (
              <button onClick={handleClear} className="btn-ghost" style={{ fontSize: 12 }}>
                Clear
              </button>
            )}
          </div>
        )}

        {/* Input area */}
        <div style={{ padding: hasSummary ? "16px 24px" : "0" }}>
          {isUrlMode && !hasSummary ? (
            <div className="flex items-center gap-3" style={{ padding: "20px 24px" }}>
              <span style={{ color: "var(--ink-tertiary)", fontSize: 18 }}>🌐</span>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="https://example.com/article"
                className="font-body"
                style={{
                  flex: 1, background: "transparent", border: "none", outline: "none",
                  fontSize: 15, color: "var(--ink-primary)", padding: "8px 0",
                }}
                autoFocus
              />
            </div>
          ) : (
            <div className={`relative ${focusMode ? "focus-target" : ""}`}>
              <textarea
                ref={textareaRef}
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setTextareaFocused(true)}
                onBlur={() => setTextareaFocused(false)}
                placeholder={hasSummary ? "" : "Paste your article, research paper, meeting notes,\nor anything up to 10,000 words...\n\n⌘V to paste instantly"}
                readOnly={hasSummary && isUrlMode}
                className="font-body"
                style={{
                  width: "100%", resize: "none", outline: "none",
                  fontSize: 15, lineHeight: 1.75,
                  background: "transparent", border: "none",
                  color: "var(--ink-primary)",
                  minHeight: hasSummary ? 120 : 320,
                  padding: "20px 24px",
                  display: "block",
                }}
              />
            </div>
          )}
        </div>

        {/* Intelligence Score Meter */}
        {!hasSummary && intelligenceScore && (
          <div style={{ padding: "0 24px" }}>
            <div className="intelligence-meter">
              <span className="font-mono" style={{ fontSize: 10, color: "var(--ink-tertiary)", textTransform: "uppercase", letterSpacing: "0.1em" }}>
                Text Complexity
              </span>
              <div className="track">
                <div className="indicator" style={{
                  left: `${intelligenceScore.pos}%`,
                  background: intelligenceScore.color,
                  boxShadow: `0 0 8px ${intelligenceScore.color}`,
                }} />
              </div>
              <span className="intelligence-meter label" style={{ color: intelligenceScore.color, textAlign: "right" }}>
                {intelligenceScore.label}
              </span>
            </div>
          </div>
        )}

        {/* ── Mode Selector (only before summary) ── */}
        {!hasSummary && (
          <div className="anim-modes" style={{ padding: "12px 24px" }}>
            <p className="section-header">Summary Mode</p>
            <div className="mode-selector">
              {MODES.map((m) => (
                <button
                  key={m.value}
                  onClick={() => handleModeSelect(m.value)}
                  className={`mode-card ${summaryMode === m.value ? "active" : ""} ${tiltMode === m.value ? "tilt" : ""}`}
                  onMouseEnter={() => setModeTooltip(m.value)}
                  onMouseLeave={() => setModeTooltip(null)}
                >
                  <span className="mode-icon">{MODE_ICONS[m.value] || m.icon}</span>
                  <span className="mode-label">{m.label}</span>
                  {/* Tooltip */}
                  {modeTooltip === m.value && (
                    <div className="tooltip visible" style={{ bottom: "calc(100% + 8px)", left: "50%", transform: "translateX(-50%)" }}>
                      {MODE_TOOLTIPS[m.value]}
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── Advanced Options ── */}
        {!hasSummary && (
          <div style={{ padding: "4px 24px 16px" }}>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="advanced-toggle"
            >
              ⚙ Advanced options
            </button>

            <div className={`advanced-content ${showAdvanced ? "open" : ""}`}>
              <div style={{ paddingTop: 12 }}>
                {/* Tone — Segmented Pill Control */}
                <p className="section-header" style={{ marginBottom: 8 }}>Tone</p>
                <div className="segmented-control" style={{ marginBottom: 16 }}>
                  {/* Sliding pill */}
                  <div className="segmented-pill" style={{
                    width: `${100 / TONES.length}%`,
                    transform: `translateX(${toneIndex * 100}%)`,
                  }} />
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

                {/* Focus Keywords */}
                <p className="section-header" style={{ marginBottom: 8 }}>
                  Focus Keywords ({focusKeywords.length}/5)
                </p>
                <div className="flex items-center gap-2 flex-wrap" style={{
                  padding: "8px 12px", borderRadius: "var(--radius-input)",
                  background: "var(--bg-input)", border: "1px solid var(--border-dim)",
                  minHeight: 36,
                }}>
                  {focusKeywords.map((kw, i) => (
                    <span key={i} className="keyword-chip">
                      {kw}
                      <button
                        onClick={() => handleRemoveKeyword(i)}
                        style={{
                          background: "none", border: "none", cursor: "pointer",
                          color: "var(--rose)", fontSize: 12, padding: 0,
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
                      placeholder="Add a keyword + Enter"
                      className="font-mono"
                      style={{
                        background: "transparent", border: "none", outline: "none",
                        fontSize: 12, color: "var(--ink-primary)", width: 140,
                      }}
                    />
                  ) : (
                    <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-tertiary)" }}>Maximum keywords added</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── Bottom Action Bar ── */}
        <div className="flex items-center justify-between flex-wrap gap-3 anim-actions" style={{
          padding: "12px 24px",
          borderTop: "1px solid var(--border-dim)",
        }}>
          {/* Left: word count + shortcut */}
          <div className="flex items-center gap-4">
            <span className="font-mono word-count-flip" key={wordCount} style={{
              fontSize: 12,
              color: getWordCountColor(wordCount),
              transition: "color 300ms var(--ease)",
            }}>
              {wordCount.toLocaleString()} words
            </span>
            {!hasSummary && (
              <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-tertiary)", opacity: 0.5 }}>
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
              <button onClick={cancelStreaming} className="btn-ghost" style={{ color: "var(--rose)" }}>
                Stop
              </button>
            )}

            {/* Summarize button */}
            <button
              onClick={onSummarize}
              disabled={isBusy}
              className="btn-primary"
              style={{ height: 44, minWidth: 150, fontSize: 16 }}
            >
              {loading ? (
                <>
                  Distilling <span className="loading-dot" style={{ marginLeft: 4 }} />
                </>
              ) : streaming ? (
                "Streaming…"
              ) : hasSummary ? (
                <>Regenerate ↺</>
              ) : (
                <>Summarize →</>
              )}
            </button>
          </div>
        </div>

        {/* Loading status words (ACT 2 of summarize ritual) */}
        {isBusy && (
          <div style={{ padding: "8px 24px 12px", textAlign: "center" }}>
            <span className="font-mono" style={{
              fontSize: 12, color: "var(--ink-tertiary)",
              animation: "statusFade 1.5s ease-in-out infinite",
              display: "inline-block",
            }}>
              {LOADING_PHASES[loadingPhase]}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}