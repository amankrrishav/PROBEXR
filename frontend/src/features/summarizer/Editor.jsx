export default function Editor({
  text,
  setText,
  loading,
  error,
  wordCount,
  charCount,
  hasSummary,
  onSummarize,
  handleKeyDown,
}) {
  return (
    <div>

      {!hasSummary && (
        <>
          <h1 className="text-3xl font-semibold tracking-tight mb-3">
            Extract signal. Ignore noise.
          </h1>

          <p className="text-gray-500 dark:text-gray-400 mb-10">
            Paste text or URL. Get the point instantly.
          </p>
        </>
      )}

      {error && (
        <div className="mb-6 text-sm text-red-500">
          {error}
        </div>
      )}

      <div className="bg-white dark:bg-[#121212] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">

        <textarea
          rows={hasSummary ? 6 : 8}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Paste article, research, or blog post..."
          className="w-full resize-none outline-none text-sm leading-relaxed bg-transparent"
        />

        <div className="flex justify-between items-center mt-6">

          <div className="text-xs text-gray-400">
            {wordCount} words · {charCount} characters
          </div>

          <button
            onClick={onSummarize}
            disabled={loading}
            className="px-6 py-2.5 rounded-full text-sm font-medium bg-black text-white dark:bg-white dark:text-black hover:opacity-90 transition disabled:opacity-50"
          >
            {loading ? "Analyzing…" : "Summarize"}
          </button>

        </div>
      </div>
    </div>
  );
}