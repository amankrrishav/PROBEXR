import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";

const LENGTH_OPTIONS = [
  { value: "brief", label: "Brief" },
  { value: "standard", label: "Standard" },
  { value: "detailed", label: "Detailed" },
];

export default function Editor({ onSummarize, handleKeyDown }) {
  const {
    text, setText, loading, loadingMessage, error, wordCount, charCount,
    hasSummary, isUrlMode, setIsUrlMode, url, setUrl,
    streaming, cancelStreaming, summaryLength, setSummaryLength,
  } = useSummarizerContext();

  const isBusy = loading || streaming;
  const isMac = typeof navigator !== "undefined" && /Mac/i.test(navigator.userAgent);

  return (
    <div>
      {/* ── Hero header (only before summary) ── */}
      {!hasSummary && (
        <div className="mb-8">
          <h1 className="text-[32px] font-semibold tracking-tight leading-tight mb-2">
            Distill what matters.
          </h1>
          <p className="text-[15px] text-gray-400 dark:text-gray-500">
            Drop in an article, paper, or blog post — get the essence in seconds.
          </p>
        </div>
      )}

      {/* ── Error ── */}
      {error && (
        <div className="mb-5 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-50 dark:bg-red-950/15 border border-red-200/60 dark:border-red-900/30 text-sm text-red-600 dark:text-red-400">
          <span className="shrink-0">⚠</span>
          {error}
        </div>
      )}

      {/* ── Input Card ── */}
      <div className="rounded-2xl border border-gray-200/80 dark:border-gray-800/80 bg-white dark:bg-[#111] overflow-hidden transition-all duration-300">

        {/* Mode switcher — only before summary */}
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
              className="text-[12px] font-medium px-4 py-1.5 rounded-lg bg-gray-900 text-white dark:bg-white dark:text-black hover:opacity-90 transition disabled:opacity-40"
            >
              {loading ? loadingMessage : streaming ? "Streaming…" : "Summarize"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}