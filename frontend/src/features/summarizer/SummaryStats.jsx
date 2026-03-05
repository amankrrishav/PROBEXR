import { useEffect, useState } from "react";

/**
 * SummaryStats — subtle inline metrics. No emojis. Clean data.
 */
export default function SummaryStats({ meta }) {
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        if (meta) {
            const t = setTimeout(() => setVisible(true), 150);
            return () => clearTimeout(t);
        }
        setVisible(false);
    }, [meta]);

    if (!meta) return null;

    const { original_word_count, summary_word_count, compression_ratio, reading_time_seconds } = meta;

    const readingStr = reading_time_seconds < 60
        ? `${reading_time_seconds}s read`
        : `${Math.round(reading_time_seconds / 60)} min read`;

    return (
        <div className={`flex items-center gap-4 transition-all duration-500 ${visible ? "opacity-100" : "opacity-0"}`}>
            <span className="text-[11px] tabular-nums text-gray-400 dark:text-gray-500">
                {original_word_count?.toLocaleString()} → {summary_word_count?.toLocaleString()} words
            </span>
            <span className="text-[11px] text-gray-300 dark:text-gray-700">·</span>
            <span className="text-[11px] tabular-nums text-gray-400 dark:text-gray-500">
                {compression_ratio}% compressed
            </span>
            <span className="text-[11px] text-gray-300 dark:text-gray-700">·</span>
            <span className="text-[11px] tabular-nums text-gray-400 dark:text-gray-500">
                {readingStr}
            </span>
        </div>
    );
}
