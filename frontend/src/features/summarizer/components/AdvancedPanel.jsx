import { useState } from "react";
import { TONES, LANGUAGES } from "../../../hooks/useSummarizer.js";

export default function AdvancedPanel({
  hasSummary,
  showAdvanced,
  setShowAdvanced,
  summaryTone,
  setSummaryTone,
  focusArea,
  setFocusArea,
  outputLanguage,
  setOutputLanguage,
  customInstructions,
  setCustomInstructions,
  focusKeywords,
  setFocusKeywords,
  resetAdvanced
}) {
  const [keywordInput, setKeywordInput] = useState("");

  if (hasSummary) return null;

  const toneIndex = TONES.findIndex(t => t.value === summaryTone);

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

  return (
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
          {/* Tone */}
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

          {/* Focus Area */}
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

          {/* Output Language */}
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

          {/* Custom Instructions */}
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
  );
}
