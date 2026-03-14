/**
 * Editor — Main input component.
 * A2: Mode pill scroll fix, fade mask, grid on desktop
 * B6: Load sample with confirm dialog, toggle to "Clear sample"  
 * B7: Word count with limit warnings
 * B8: Length selector with visual active state
 * B9: URL tab validation, loading state, error
 * B10: Advanced options — focus area, language, custom instructions
 * B11: New Summary fully resets + focuses textarea
 * C1: Summarize button loading/success/error states
 */
import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";
import { useAppContext } from "../../contexts/AppContext.jsx";
import { MODES, TONES, LANGUAGES } from "../../hooks/useSummarizer.js";

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

/* ── Intelligence Score Calculation ── */
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

/* ── Word Count Color (B7) ── */
function getWordCountColor(count) {
  if (count === 0) return "var(--ink-tertiary)";
  if (count > 10000) return "var(--rose)";
  if (count > 8000) return "var(--amber)";
  if (count <= 50) return "var(--amber)";
  if (count <= 500) return "var(--sage)";
  return "var(--ink-secondary)";
}

function getWordCountTooltip(count) {
  if (count > 10000) return "Over 10,000 word limit";
  if (count > 8000) return "Approaching limit";
  return null;
}

export default function Editor({ onSummarize, handleKeyDown, focusMode }) {
  const {
    text, setText, loading, loadingMessage, error, wordCount, charCount,
    hasSummary, isUrlMode, setIsUrlMode, url, setUrl,
    streaming, cancelStreaming, summaryLength, setSummaryLength,
    summaryMode, setSummaryMode, summaryTone, setSummaryTone,
    focusKeywords, setFocusKeywords,
    focusArea, setFocusArea, outputLanguage, setOutputLanguage,
    customInstructions, setCustomInstructions, resetAdvanced,
    summarizeStatus, textareaRef,
  } = useSummarizerContext();

  const { providerStatus, summaryHistory } = useAppContext();

  const [keywordInput, setKeywordInput] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [textareaFocused, setTextareaFocused] = useState(false);
  const [tiltMode, setTiltMode] = useState(null);
  const [loadingPhase, setLoadingPhase] = useState(0);
  const [modeTooltip, setModeTooltip] = useState(null);
  const [isSampleLoaded, setIsSampleLoaded] = useState(false);
  const [urlError, setUrlError] = useState(null);
  const [modeScrollFaded, setModeScrollFaded] = useState(true);
  const modeScrollRef = useRef(null);

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

  // Auto-grow textarea
  useEffect(() => {
    const ta = textareaRef?.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, window.innerHeight * 0.6) + "px";
  }, [text, textareaRef]);

  // Track sample text state
  useEffect(() => {
    setIsSampleLoaded(text === SAMPLE_TEXT);
  }, [text]);

  // Mode scroll fade mask (A2)
  function handleModeScroll() {
    const el = modeScrollRef.current;
    if (!el) return;
    const atEnd = el.scrollLeft + el.clientWidth >= el.scrollWidth - 2;
    setModeScrollFaded(!atEnd);
  }

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

  // B6: Load sample with confirm
  function handleLoadSample() {
    if (text.trim() && text !== SAMPLE_TEXT) {
      if (!window.confirm("This will replace your current text. Continue?")) return;
    }
    setText(SAMPLE_TEXT);
    setIsUrlMode(false);
    setIsSampleLoaded(true);
  }

  // B6: Clear sample
  function handleClearSample() {
    setText("");
    setUrl("");
    setIsSampleLoaded(false);
  }

  function handleClear() {
    setText("");
    setUrl("");
    setIsSampleLoaded(false);
  }

  function handleModeSelect(mode) {
    setTiltMode(mode);
    setSummaryMode(mode);
    setTimeout(() => setTiltMode(null), 300);
  }

  // URL validation on blur (B9)
  function handleUrlBlur() {
    if (url.trim()) {
      try {
        new URL(url.trim());
        setUrlError(null);
      } catch {
        setUrlError("Please enter a valid URL (e.g. https://example.com)");
      }
    } else {
      setUrlError(null);
    }
  }

  // Enhanced summarize (C1 + B3/B4 history)
  function handleSummarizeClick() {
    // B9: URL validation before submit
    if (isUrlMode && url.trim()) {
      try {
        new URL(url.trim());
      } catch {
        setUrlError("Please enter a valid URL (e.g. https://example.com)");
        return;
      }
    }
    onSummarize();
  }

  // Compute the active tone segment index for the sliding pill
  const toneIndex = TONES.findIndex(t => t.value === summaryTone);
  const wordCountTooltip = getWordCountTooltip(wordCount);

  // Button label (C1)
  function getSummarizeButtonContent() {
    if (loading) {
      return (
        <>
          <span style={{
            width: 14, height: 14,
            border: "2px solid rgba(11,9,6,0.3)",
            borderTopColor: "#0B0906",
            borderRadius: "50%",
            animation: "spin 600ms linear infinite",
            display: "inline-block",
          }} />
          Summarizing...
        </>
      );
    }
    if (streaming) return "Streaming…";
    if (summarizeStatus === "success") return <>✓ Done</>;
    if (summarizeStatus === "error") return <>✗ Failed</>;
    if (hasSummary) return <>Regenerate ↺</>;
    return <>Summarize →</>;
  }

  function getSummarizeButtonStyle() {
    const base = { height: 44, minWidth: 150, fontSize: 16 };
    if (summarizeStatus === "success") {
      return { ...base, background: "var(--sage)", boxShadow: "0 0 12px rgba(110,186,127,0.3)" };
    }
    if (summarizeStatus === "error") {
      return { ...base, background: "var(--rose)", boxShadow: "0 0 12px rgba(224,92,92,0.3)" };
    }
    return base;
  }

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

      {/* ── Error (C1) ── */}
      {error && (
        <div className="flex items-center gap-2 animate-in" style={{
          padding: "12px 16px", borderRadius: "var(--radius-btn)", marginBottom: 16,
          background: "rgba(224,92,92,0.08)", border: "1px solid rgba(224,92,92,0.2)",
          fontSize: 13, color: "var(--rose)",
          justifyContent: "space-between",
        }}>
          <div className="flex items-center gap-2">
            <span>⚠</span> {error}
          </div>
          <button
            onClick={handleSummarizeClick}
            className="btn-ghost"
            style={{ fontSize: 12, color: "var(--amber)", flexShrink: 0 }}
          >
            Retry
          </button>
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

            {/* B6: Load sample / Clear sample toggle */}
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
        )}

        {/* Input area */}
        <div style={{ padding: hasSummary ? "16px 24px" : "0" }}>
          {isUrlMode && !hasSummary ? (
            <div style={{ padding: "20px 24px" }}>
              <div className="flex items-center gap-3">
                <span style={{ color: "var(--ink-tertiary)", fontSize: 18 }}>🌐</span>
                <input
                  type="url"
                  value={url}
                  onChange={(e) => { setUrl(e.target.value); setUrlError(null); }}
                  onKeyDown={handleKeyDown}
                  onBlur={handleUrlBlur}
                  placeholder="https://example.com/article"
                  className="font-body"
                  style={{
                    flex: 1, background: "transparent",
                    border: "none", outline: "none",
                    fontSize: 15, color: "var(--ink-primary)", padding: "8px 0",
                    borderBottom: urlError ? "1px solid var(--rose)" : "none",
                  }}
                  autoFocus
                  aria-label="URL to summarize"
                />
              </div>
              {urlError && (
                <p className="font-mono" style={{ fontSize: 11, color: "var(--rose)", marginTop: 6 }}>
                  {urlError}
                </p>
              )}
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
                aria-label="Text input"
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

        {/* ── Mode Selector (A2: scroll fix + grid on desktop) ── */}
        {!hasSummary && (
          <div className="anim-modes" style={{ padding: "12px 24px" }}>
            <p className="section-header">Summary Mode</p>
            <div
              ref={modeScrollRef}
              onScroll={handleModeScroll}
              className="mode-selector-wrap"
              style={{ position: "relative" }}
            >
              <div className="mode-selector">
                {MODES.map((m) => (
                  <button
                    key={m.value}
                    onClick={() => handleModeSelect(m.value)}
                    className={`mode-card ${summaryMode === m.value ? "active" : ""} ${tiltMode === m.value ? "tilt" : ""}`}
                    onMouseEnter={() => setModeTooltip(m.value)}
                    onMouseLeave={() => setModeTooltip(null)}
                    aria-label={`${m.label}: ${MODE_TOOLTIPS[m.value]}`}
                  >
                    <span className="mode-icon">{MODE_ICONS[m.value] || m.icon}</span>
                    <span className="mode-label">{m.label}</span>
                    {modeTooltip === m.value && (
                      <div className="tooltip visible" style={{ bottom: "calc(100% + 8px)", left: "50%", transform: "translateX(-50%)" }}>
                        {MODE_TOOLTIPS[m.value]}
                      </div>
                    )}
                  </button>
                ))}
              </div>
              {/* Fade mask (A2) */}
              {modeScrollFaded && (
                <div className="mode-fade-mask" style={{
                  position: "absolute", right: 0, top: 0, bottom: 0,
                  width: 48,
                  background: "linear-gradient(to right, transparent, var(--bg-surface))",
                  pointerEvents: "none",
                  zIndex: 2,
                }} />
              )}
            </div>
          </div>
        )}

        {/* ── Advanced Options (B10) ── */}
        {!hasSummary && (
          <div style={{ padding: "4px 24px 16px" }}>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="advanced-toggle"
              aria-expanded={showAdvanced}
            >
              ⚙ Advanced options {showAdvanced ? "▴" : "▾"}
            </button>

            <div className={`advanced-content ${showAdvanced ? "open" : ""}`}>
              <div style={{ paddingTop: 12 }}>
                {/* Tone — Segmented Pill Control */}
                <p className="section-header" style={{ marginBottom: 8 }}>Tone</p>
                <div className="segmented-control" style={{ marginBottom: 16 }}>
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

                {/* Focus Area (B10) */}
                <p className="section-header" style={{ marginBottom: 8 }}>Focus Area</p>
                <input
                  type="text"
                  value={focusArea}
                  onChange={(e) => setFocusArea(e.target.value)}
                  placeholder="Focus on a specific aspect, e.g. 'financial risks'"
                  className="font-body"
                  style={{
                    width: "100%", padding: "8px 12px",
                    borderRadius: "var(--radius-input)",
                    background: "var(--bg-input)", border: "1px solid var(--border-dim)",
                    color: "var(--ink-primary)", fontSize: 13, outline: "none",
                    marginBottom: 16,
                  }}
                  aria-label="Focus area"
                />

                {/* Output Language (B10) */}
                <p className="section-header" style={{ marginBottom: 8 }}>Output Language</p>
                <select
                  value={outputLanguage}
                  onChange={(e) => setOutputLanguage(e.target.value)}
                  className="font-body"
                  style={{
                    width: "100%", padding: "8px 12px",
                    borderRadius: "var(--radius-input)",
                    background: "var(--bg-input)", border: "1px solid var(--border-dim)",
                    color: "var(--ink-primary)", fontSize: 13, outline: "none",
                    marginBottom: 16, cursor: "pointer",
                    appearance: "none",
                    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%235A5048' d='M3 4.5L6 8l3-3.5z'/%3E%3C/svg%3E")`,
                    backgroundRepeat: "no-repeat",
                    backgroundPosition: "right 12px center",
                  }}
                  aria-label="Output language"
                >
                  {LANGUAGES.map((lang) => (
                    <option key={lang} value={lang}>{lang}</option>
                  ))}
                </select>

                {/* Custom Instructions (B10) */}
                <p className="section-header" style={{ marginBottom: 8 }}>
                  Custom Instructions ({customInstructions.length}/200)
                </p>
                <textarea
                  value={customInstructions}
                  onChange={(e) => {
                    if (e.target.value.length <= 200) setCustomInstructions(e.target.value);
                  }}
                  placeholder="Add custom instructions for the AI..."
                  className="font-body"
                  style={{
                    width: "100%", padding: "8px 12px",
                    borderRadius: "var(--radius-input)",
                    background: "var(--bg-input)", border: "1px solid var(--border-dim)",
                    color: "var(--ink-primary)", fontSize: 13, outline: "none",
                    resize: "none", minHeight: 60, marginBottom: 16,
                  }}
                  maxLength={200}
                  aria-label="Custom instructions"
                />

                {/* Focus Keywords */}
                <p className="section-header" style={{ marginBottom: 8 }}>
                  Focus Keywords ({focusKeywords.length}/5)
                </p>
                <div className="flex items-center gap-2 flex-wrap" style={{
                  padding: "8px 12px", borderRadius: "var(--radius-input)",
                  background: "var(--bg-input)", border: "1px solid var(--border-dim)",
                  minHeight: 36, marginBottom: 12,
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
                        aria-label={`Remove keyword ${kw}`}
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

                {/* Reset to defaults */}
                <button
                  onClick={resetAdvanced}
                  className="font-mono"
                  style={{
                    background: "none", border: "none", cursor: "pointer",
                    fontSize: 11, color: "var(--ink-tertiary)",
                    textDecoration: "underline",
                    padding: 0,
                  }}
                >
                  Reset to defaults
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Bottom Action Bar ── */}
        <div className="flex items-center justify-between flex-wrap gap-3 anim-actions" style={{
          padding: "12px 24px",
          borderTop: "1px solid var(--border-dim)",
        }}>
          {/* Left: word count + shortcut (B7) */}
          <div className="flex items-center gap-4">
            <span
              className="font-mono word-count-flip"
              key={wordCount}
              title={wordCountTooltip || ""}
              style={{
                fontSize: 12,
                color: getWordCountColor(wordCount),
                transition: "color 300ms var(--ease)",
              }}
            >
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
            {/* Length selector (B8) */}
            {!hasSummary && (
              <div className="segmented-control">
                {LENGTH_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setSummaryLength(opt.value)}
                    className={summaryLength === opt.value ? "active" : ""}
                    aria-label={`Length: ${opt.label}`}
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

            {/* Summarize button (C1) */}
            <button
              onClick={handleSummarizeClick}
              disabled={isBusy || providerStatus.status === "offline"}
              className="btn-primary"
              style={getSummarizeButtonStyle()}
              title={providerStatus.status === "offline" ? "Provider unavailable" : ""}
            >
              {getSummarizeButtonContent()}
            </button>
          </div>
        </div>

        {/* Loading status words */}
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