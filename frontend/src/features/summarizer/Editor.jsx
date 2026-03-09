import { useState } from "react";
import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";
import { MODES, TONES } from "../../hooks/useSummarizer.js";

const LENGTH_OPTIONS = [
  { value: "brief", label: "Short" },
  { value: "standard", label: "Medium" },
  { value: "detailed", label: "Long" },
];

const SAMPLE_TEXT = `Artificial intelligence has rapidly transformed from a research curiosity into a cornerstone of modern technology. In the past decade, advances in deep learning, natural language processing, and computer vision have enabled applications that were previously considered science fiction. Self-driving cars navigate complex urban environments, language models generate human-quality text, and AI systems diagnose diseases with accuracy rivaling experienced physicians.

However, this rapid advancement has also raised significant concerns. Issues of bias in training data, the environmental cost of training large models, and the potential for job displacement have sparked intense debate among policymakers, technologists, and the public. The concentration of AI capabilities in a small number of large technology companies has also raised questions about market power and democratic governance of transformative technologies.

Looking forward, the field faces critical decisions about safety, alignment, and regulation. Researchers are increasingly focused on developing AI systems that are not only capable but also trustworthy, transparent, and aligned with human values. The next decade will likely determine whether AI becomes a tool for broad human flourishing or a source of deepening inequality and existential risk.`;

export default function Editor({ onSummarize, handleKeyDown }) {
  const {
    text, setText, loading, loadingMessage, error, wordCount,
    hasSummary, isUrlMode, setIsUrlMode, url, setUrl,
    streaming, cancelStreaming, summaryLength, setSummaryLength,
    summaryMode, setSummaryMode, summaryTone, setSummaryTone,
    focusKeywords, setFocusKeywords,
  } = useSummarizerContext();

  const [keywordInput, setKeywordInput] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
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

  return (
    <div className="space-y-4">
      {/* ── Hero header (only before summary) ── */}
      {!hasSummary && (
        <div className="mb-6">
          <h1 className="text-[28px] sm:text-[32px] font-semibold tracking-tight leading-tight mb-2">
            Distill what matters.
          </h1>
          <p className="text-[14px] text-gray-400 dark:text-gray-500">
            Drop in an article, paper, or blog post — get the essence in seconds.
          </p>
        </div>
      )}

      {/* ── Error ── */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-50 dark:bg-red-950/15 border border-red-200/60 dark:border-red-900/30 text-sm text-red-600 dark:text-red-400">
          <span className="shrink-0">⚠</span>
          {error}
        </div>
      )}

      {/* ── Input Card ── */}
      <div className="rounded-2xl border border-gray-200/80 dark:border-gray-800/80 bg-white dark:bg-[#111] overflow-hidden transition-all duration-300">

        {/* Mode switcher tabs — only before summary */}
        {!hasSummary && (
          <div className="flex items-center gap-1 px-5 pt-4 pb-0">
            <button
              onClick={() => setIsUrlMode(false)}
              className={`text-[12px] font-medium px-3 py-1.5 rounded-md transition-all ${!isUrlMode
                ? "bg-gray-900 text-white dark:bg-white dark:text-black"
                : "text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
                }`}
            >
              Text
            </button>
            <button
              onClick={() => setIsUrlMode(true)}
              className={`text-[12px] font-medium px-3 py-1.5 rounded-md transition-all ${isUrlMode
                ? "bg-gray-900 text-white dark:bg-white dark:text-black"
                : "text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
                }`}
            >
              URL
            </button>
            {/* Sample text button */}
            {!isUrlMode && !text && (
              <button
                onClick={handleLoadSample}
                className="ml-auto text-[11px] font-medium px-2.5 py-1 rounded-md text-teal-500 hover:bg-teal-50 dark:hover:bg-teal-900/20 transition"
              >
                Load sample
              </button>
            )}
          </div>
        )}

        {/* Input area */}
        <div className="px-5 pt-4 pb-3">
          {isUrlMode && !hasSummary ? (
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="https://example.com/article"
              className="w-full bg-transparent text-[15px] outline-none placeholder:text-gray-300 dark:placeholder:text-gray-600"
              autoFocus
            />
          ) : (
            <textarea
              rows={hasSummary ? 5 : 7}
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={hasSummary ? "" : "Paste your text here…"}
              readOnly={hasSummary && isUrlMode}
              className="w-full resize-none outline-none text-[14px] leading-[1.7] bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-600"
            />
          )}
        </div>

        {/* ── Summary Mode selector ── */}
        {!hasSummary && (
          <div className="px-5 pb-3">
            <div className="flex items-center gap-1.5 flex-wrap">
              {MODES.map((m) => (
                <button
                  key={m.value}
                  onClick={() => setSummaryMode(m.value)}
                  className={`text-[11px] font-medium px-2.5 py-1.5 rounded-lg transition-all ${summaryMode === m.value
                    ? "bg-teal-500/10 text-teal-600 dark:text-teal-400 border border-teal-300/50 dark:border-teal-700/50"
                    : "text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 border border-transparent hover:border-gray-200 dark:hover:border-gray-700"
                    }`}
                >
                  <span className="mr-1">{m.icon}</span>{m.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── Advanced controls toggle ── */}
        {!hasSummary && (
          <div className="px-5 pb-3">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-[11px] font-medium text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition flex items-center gap-1"
            >
              <span className={`transition-transform duration-200 text-[9px] ${showAdvanced ? "rotate-90" : ""}`}>▸</span>
              Advanced options
            </button>

            {showAdvanced && (
              <div className="mt-3 space-y-3 pl-2 border-l-2 border-gray-100 dark:border-gray-800">
                {/* Tone selector */}
                <div>
                  <label className="block text-[10px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-1.5">Tone</label>
                  <div className="flex items-center gap-1.5">
                    {TONES.map((t) => (
                      <button
                        key={t.value}
                        onClick={() => setSummaryTone(t.value)}
                        className={`text-[11px] font-medium px-2.5 py-1 rounded-md transition-all ${summaryTone === t.value
                          ? "bg-gray-900 text-white dark:bg-white dark:text-black"
                          : "text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
                          }`}
                      >
                        {t.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Keywords */}
                <div>
                  <label className="block text-[10px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-1.5">
                    Focus Keywords <span className="font-normal">({focusKeywords.length}/5)</span>
                  </label>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {focusKeywords.map((kw, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-teal-50 dark:bg-teal-900/20 text-teal-600 dark:text-teal-400 border border-teal-200/50 dark:border-teal-700/50"
                      >
                        {kw}
                        <button onClick={() => handleRemoveKeyword(i)} className="hover:text-red-500 transition">×</button>
                      </span>
                    ))}
                    {focusKeywords.length < 5 && (
                      <input
                        type="text"
                        value={keywordInput}
                        onChange={(e) => setKeywordInput(e.target.value)}
                        onKeyDown={handleAddKeyword}
                        placeholder="Type + Enter"
                        className="text-[11px] w-24 bg-transparent outline-none placeholder:text-gray-300 dark:placeholder:text-gray-600"
                      />
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Footer bar */}
        <div className="flex items-center justify-between px-5 py-3 border-t border-gray-100 dark:border-gray-800/60">
          {/* Left: word count */}
          <div className="flex items-center gap-3">
            <span className="text-[11px] tabular-nums text-gray-400 dark:text-gray-500">
              {wordCount.toLocaleString()} words
            </span>
            {!hasSummary && (
              <span className="text-[11px] text-gray-300 dark:text-gray-700">
                {isMac ? "⌘" : "Ctrl"}+Enter to summarize
              </span>
            )}
          </div>

          {/* Right: controls */}
          <div className="flex items-center gap-2">
            {/* Length selector */}
            {!hasSummary && (
              <div className="flex items-center rounded-lg border border-gray-200/80 dark:border-gray-800/80 overflow-hidden">
                {LENGTH_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setSummaryLength(opt.value)}
                    className={`text-[11px] font-medium px-2.5 py-1 transition-all ${summaryLength === opt.value
                      ? "bg-gray-900 text-white dark:bg-white dark:text-black"
                      : "text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
                      }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}

            {/* Cancel */}
            {streaming && (
              <button
                onClick={cancelStreaming}
                className="text-[12px] font-medium px-3 py-1.5 rounded-lg text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition"
              >
                Stop
              </button>
            )}

            {/* Summarize */}
            <button
              onClick={onSummarize}
              disabled={isBusy}
              className="text-[12px] font-medium px-4 py-1.5 rounded-lg bg-teal-500 text-white hover:bg-teal-600 transition disabled:opacity-40 shadow-sm shadow-teal-500/20"
            >
              {loading ? loadingMessage : streaming ? "Streaming…" : "Summarize"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}