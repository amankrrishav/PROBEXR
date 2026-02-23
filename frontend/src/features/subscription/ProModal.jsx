export default function ProModal({ open, onClose, onUpgrade, submitting, error }) {
  if (!open) return null;

  async function handleUpgrade() {
    try {
      await onUpgrade();
    } catch {
      // error handled via error prop
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="relative w-full max-w-md rounded-2xl bg-white/95 p-6 shadow-2xl dark:bg-[#111111]/95 border border-gray-200 dark:border-gray-800">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
        >
          Esc
        </button>

        <h2 className="text-lg font-semibold tracking-tight">
          Pro Mode (demo)
        </h2>
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          Unlock high-quality LLM summaries all day. No billing yet — this is a demo Pro
          mode so you can test the full experience before pricing.
        </p>

        <div className="mt-4 space-y-2 text-xs text-gray-600 dark:text-gray-300">
          <div className="flex items-start gap-2">
            <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-emerald-400" />
            <p>Full-quality LLM summaries beyond the free daily limit.</p>
          </div>
          <div className="flex items-start gap-2">
            <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-emerald-400" />
            <p>Perfect for daily readers, writers, and internet-heavy workflows.</p>
          </div>
          <div className="flex items-start gap-2">
            <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-emerald-400" />
            <p>Designed to scale later into real subscriptions and team plans.</p>
          </div>
        </div>

        {error && (
          <p className="mt-3 text-[11px] text-red-500">
            {error}
          </p>
        )}

        <button
          type="button"
          onClick={handleUpgrade}
          disabled={submitting}
          className="mt-4 inline-flex w-full items-center justify-center rounded-full bg-black px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70 dark:bg-white dark:text-black"
        >
          {submitting ? "Activating Pro Mode…" : "Activate Pro Mode (demo)"}
        </button>

        <p className="mt-2 text-[10px] text-gray-400">
          This is a demo toggle — no payment is collected. Later we can connect it to real billing.
        </p>
      </div>
    </div>
  );
}

