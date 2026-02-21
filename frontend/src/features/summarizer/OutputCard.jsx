import TypingSummary from "./TypingSummary";

export default function OutputCard({ summaryText }) {
  return (
    <div className="bg-white dark:bg-[#121212] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">

      <h3 className="text-xs uppercase tracking-wider text-gray-400 mb-6">
        Summary
      </h3>

      <TypingSummary text={summaryText} />

    </div>
  );
}