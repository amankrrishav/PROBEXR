import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";

const LENGTH_OPTIONS = [
  { value: "brief", label: "Brief", desc: "~1 paragraph" },
  { value: "standard", label: "Standard", desc: "~2 paragraphs" },
  { value: "detailed", label: "Detailed", desc: "~4 paragraphs" },
];

export default function Editor({
  onSummarize,
  handleKeyDown,
}) {
  const {
    text,
    setText,
    loading,
    loadingMessage,
    error,
    wordCount,
    charCount,
    hasSummary,
    isUrlMode,
    setIsUrlMode,
    url,
    setUrl,
    streaming,
    cancelStreaming,
    summaryLength,
    setSummaryLength,
  } = useSummarizerContext();

  const isBusy = loading || streaming;

  return (
    <div>

      {!hasSummary && (
        <>
          <h1 className="text-3xl font-semibold tracking-tight mb-3">
            Extract signal. Ignore noise.
          </h1>

          <p className="text-gray-500 dark:text-gray-400 mb-10">
            Paste text. Get the point instantly.
          </p>
        </>
      )}

      {error && (
        <div className="mb-6 text-sm text-red-500">
          {error}
        </div>
      )}

      <div className="bg-white dark:bg-[#121212] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm transition-all duration-300">
        {!hasSummary && (
          <div className="flex gap-4 mb-4 border-b border-gray-200 dark:border-gray-800 pb-4">
            <button
              onClick={() => setIsUrlMode(false)}
              className={`text-sm font-medium px-4 py-2 rounded-lg transition-colors ${!isUrlMode
                ? "bg-gray-100 text-black dark:bg-gray-800 dark:text-white"
                : "text-gray-500 hover:text-black dark:text-gray-400 dark:hover:text-white"
                }`}
            >
              Paste Text
            </button>
            <button
              onClick={() => setIsUrlMode(true)}
              className={`text-sm font-medium px-4 py-2 rounded-lg transition-colors ${isUrlMode
                ? "bg-gray-100 text-black dark:bg-gray-800 dark:text-white"
                : "text-gray-500 hover:text-black dark:text-gray-400 dark:hover:text-white"
                }`}
            >
              Paste URL
            </button>
          </div>
        )}

        {isUrlMode && !hasSummary ? (
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="https://example.com/article"
            className="w-full bg-gray-50 dark:bg-[#1A1A1A] border border-gray-200 dark:border-gray-800 rounded-xl px-4 py-3 outline-none text-sm transition-colors focus:border-black dark:focus:border-white mb-4"
          />
        ) : (
          <textarea
            rows={hasSummary ? 6 : 8}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={hasSummary ? "Original Text" : "Paste article, research, or blog post..."}
            readOnly={hasSummary && isUrlMode}
            className="w-full resize-none outline-none text-sm leading-relaxed bg-transparent"
          />
        )}

        <div className="flex justify-between items-center mt-6">

          <div className="text-xs text-gray-400">
            {wordCount} words · {charCount} characters
          </div>

          <div className="flex items-center gap-3">
            {/* Length selector — only show when no summary yet */}
            {!hasSummary && (
              <div className="flex rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
                {LENGTH_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setSummaryLength(opt.value)}
                    title={opt.desc}
                    className={`text-[11px] font-medium px-3 py-1.5 transition-colors ${summaryLength === opt.value
                        ? "bg-black text-white dark:bg-white dark:text-black"
                        : "text-gray-500 hover:text-black dark:text-gray-400 dark:hover:text-white bg-transparent"
                      }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}

            {streaming && (
              <button
                onClick={cancelStreaming}
                className="px-5 py-2.5 rounded-full text-sm font-medium border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition"
              >
                Cancel
              </button>
            )}
            <button
              onClick={onSummarize}
              disabled={isBusy}
              className="px-6 py-2.5 rounded-full text-sm font-medium bg-black text-white dark:bg-white dark:text-black hover:opacity-90 transition disabled:opacity-50"
            >
              {loading ? loadingMessage : streaming ? "Streaming…" : "Summarize"}
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}