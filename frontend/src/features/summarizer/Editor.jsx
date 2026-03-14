/**
 * Editor — Main input component.
 * Refactored into sub-components for maintainability.
 */
import { useState, useRef, useEffect } from "react";
import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";
import { useAppContext } from "../../contexts/AppContext.jsx";

// Modularized sub-components
import ComplexityMeter from "./components/ComplexityMeter.jsx";
import ModeSelector from "./components/ModeSelector.jsx";
import AdvancedPanel from "./components/AdvancedPanel.jsx";
import InputTabs from "./components/InputTabs.jsx";

const LENGTH_OPTIONS = [
  { value: "brief", label: "Short" },
  { value: "standard", label: "Medium" },
  { value: "detailed", label: "Long" },
];

const SAMPLE_TEXT = `Artificial intelligence has rapidly transformed from a research curiosity into a cornerstone of modern technology. In the past decade, advances in deep learning, natural language processing, and computer vision have enabled applications that were previously considered science fiction. Self-driving cars navigate complex urban environments, language models generate human-quality text, and AI systems diagnose diseases with accuracy rivaling experienced physicians.

However, this rapid advancement has also raised significant concerns. Issues of bias in training data, the environmental cost of training large models, and the potential for job displacement have sparked intense debate among policymakers, technologists, and the public. The concentration of AI capabilities in a small number of large technology companies has also raised questions about market power and democratic governance of transformative technologies.

Looking forward, the field faces critical decisions about safety, alignment, and regulation. Researchers are increasingly focused on developing AI systems that are not only capable but also trustworthy, transparent, and aligned with human values. The next decade will likely determine whether AI becomes a tool for broad human flourishing or a source of deepening inequality and existential risk.`;

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
    text, setText, loading, streaming, cancelStreaming, wordCount,
    hasSummary, isUrlMode, setIsUrlMode, url, setUrl,
    summaryLength, setSummaryLength,
    summaryMode, setSummaryMode, summaryTone, setSummaryTone,
    focusKeywords, setFocusKeywords,
    focusArea, setFocusArea, outputLanguage, setOutputLanguage,
    customInstructions, setCustomInstructions, resetAdvanced,
    summarizeStatus, textareaRef, error
  } = useSummarizerContext();

  const { providerStatus } = useAppContext();

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [textareaFocused, setTextareaFocused] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState(0);
  const [isSampleLoaded, setIsSampleLoaded] = useState(false);
  const [urlError, setUrlError] = useState(null);

  const isBusy = loading || streaming;
  const isMac = typeof navigator !== "undefined" && /Mac/i.test(navigator.userAgent);
  const LOADING_PHASES = ["Reading...", "Extracting...", "Structuring...", "Refining..."];

  // Rotate loading phases
  useEffect(() => {
    if (!isBusy) return;
    setLoadingPhase(0);
    let i = 0;
    const interval = setInterval(() => {
      i = (i + 1) % 4; // Use 4 instead of LOADING_PHASES.length to avoid missing dependency warning
      setLoadingPhase(i);
    }, 1500);
    return () => clearInterval(interval);
  }, [isBusy]);

  // Auto-grow textarea
  useEffect(() => {
    if (textareaRef && textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, window.innerHeight * 0.6) + "px";
    }
  }, [text, textareaRef]);

  useEffect(() => {
    setIsSampleLoaded(text === SAMPLE_TEXT);
  }, [text]);

  function handleLoadSample() {
    if (text.trim() && text !== SAMPLE_TEXT) {
      if (!window.confirm("This will replace your current text. Continue?")) return;
    }
    setText(SAMPLE_TEXT);
    setIsUrlMode(false);
    setIsSampleLoaded(true);
  }

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

  function handleSummarizeClick() {
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
      {/* ── Hero header ── */}
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
          justifyContent: "space-between",
        }}>
          <div className="flex items-center gap-2">
            <span>⚠</span> {error}
          </div>
          <button onClick={handleSummarizeClick} className="btn-ghost" style={{ fontSize: 12, color: "var(--amber)", flexShrink: 0 }}>
            Retry
          </button>
        </div>
      )}

      {/* ── Input Card ── */}
      <div className={`card anim-input ${textareaFocused ? "card-focused" : ""}`} style={{ position: "relative", overflow: "hidden" }}>
        {isBusy && <div className="progress-line" />}

        <InputTabs 
          hasSummary={hasSummary}
          isUrlMode={isUrlMode}
          setIsUrlMode={setIsUrlMode}
          text={text}
          setText={setText}
          url={url}
          setUrl={setUrl}
          isSampleLoaded={isSampleLoaded}
          setIsSampleLoaded={setIsSampleLoaded}
          handleLoadSample={handleLoadSample}
          handleClearSample={handleClearSample}
          handleClear={handleClear}
        />

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
                />
              </div>
              {urlError && <p className="font-mono" style={{ fontSize: 11, color: "var(--rose)", marginTop: 6 }}>{urlError}</p>}
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
                placeholder={hasSummary ? "" : "Paste your article...\n\n⌘V to paste instantly"}
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

        <ComplexityMeter text={text} hasSummary={hasSummary} />

        <ModeSelector 
          summaryMode={summaryMode} 
          setSummaryMode={setSummaryMode} 
          hasSummary={hasSummary} 
        />

        <AdvancedPanel 
          hasSummary={hasSummary}
          showAdvanced={showAdvanced}
          setShowAdvanced={setShowAdvanced}
          summaryTone={summaryTone}
          setSummaryTone={setSummaryTone}
          focusArea={focusArea}
          setFocusArea={setFocusArea}
          outputLanguage={outputLanguage}
          setOutputLanguage={setOutputLanguage}
          customInstructions={customInstructions}
          setCustomInstructions={setCustomInstructions}
          focusKeywords={focusKeywords}
          setFocusKeywords={setFocusKeywords}
          resetAdvanced={resetAdvanced}
        />

        <div className="flex items-center justify-between flex-wrap gap-3 anim-actions" style={{
          padding: "12px 24px",
          borderTop: "1px solid var(--border-dim)",
        }}>
          <div className="flex items-center gap-4">
            <span className="font-mono word-count-flip" key={wordCount} style={{ fontSize: 12, color: getWordCountColor(wordCount) }}>
              {wordCount.toLocaleString()} words
            </span>
            {!hasSummary && <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-tertiary)", opacity: 0.5 }}>{isMac ? "⌘" : "Ctrl"}+Enter</span>}
          </div>

          <div className="flex items-center gap-3">
            {!hasSummary && (
              <div className="segmented-control">
                {LENGTH_OPTIONS.map((opt) => (
                  <button key={opt.value} onClick={() => setSummaryLength(opt.value)} className={summaryLength === opt.value ? "active" : ""}>
                    {opt.label}
                  </button>
                ))}
              </div>
            )}
            {streaming && <button onClick={cancelStreaming} className="btn-ghost" style={{ color: "var(--rose)" }}>Stop</button>}
            <button
              onClick={handleSummarizeClick}
              disabled={isBusy || providerStatus.status === "offline"}
              className="btn-primary"
              style={getSummarizeButtonStyle()}
            >
              {getSummarizeButtonContent()}
            </button>
          </div>
        </div>

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