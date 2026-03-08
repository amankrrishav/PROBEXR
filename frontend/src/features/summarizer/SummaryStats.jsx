import { useEffect, useState } from "react";

/**
 * SummaryStats — subtle inline metrics with content type and readability.
 */

const CONTENT_TYPE_LABELS = {
    academic: "Academic",
    news: "News",
    technical: "Technical",
    opinion: "Opinion",
    general: "General",
};

const READABILITY_COLORS = {
    "Very Easy": "text-emerald-500",
    "Easy": "text-emerald-500",
    "Average": "text-gray-400 dark:text-gray-500",
    "Moderate": "text-amber-500",
    "Difficult": "text-orange-500",
    "Very Difficult": "text-red-500",
};

export default function SummaryStats({ meta }) {
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setVisible(false);
        if (meta) {
            const t = setTimeout(() => setVisible(true), 150);
            return () => clearTimeout(t);
        }
    }, [meta]);

    if (!meta) return null;

    const {
        original_word_count,
        summary_word_count,
        compression_ratio,
        reading_time_seconds,
        content_type,
        readability_label,
    } = meta;

    const readingStr = reading_time_seconds < 60
        ? `${reading_time_seconds}s read`
        : `${Math.round(reading_time_seconds / 60)} min read`;

    const typeLabel = CONTENT_TYPE_LABELS[content_type] || null;
    const readabilityColor = READABILITY_COLORS[readability_label] || "text-gray-400";

    return (
        <div className={`flex items-center gap-3 flex-wrap transition-all duration-500 ${visible ? "opacity-100" : "opacity-0"}`}>
            {/* Content type badge */}
            {typeLabel && typeLabel !== "General" && (
                <>
                    <span className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-gray-100 dark:bg-gray-800/60 text-gray-500 dark:text-gray-400">
                        {typeLabel}
                    </span>
                    <span className="text-[11px] text-gray-200 dark:text-gray-800">·</span>
                </>
            )}

            <span className="text-[11px] tabular-nums text-gray-400 dark:text-gray-500">
                {original_word_count?.toLocaleString()} → {summary_word_count?.toLocaleString()} words
            </span>
            <span className="text-[11px] text-gray-200 dark:text-gray-800">·</span>
            <span className="text-[11px] tabular-nums text-gray-400 dark:text-gray-500">
                {compression_ratio}% compressed
            </span>
            <span className="text-[11px] text-gray-200 dark:text-gray-800">·</span>
            {/* Reading Time */}
            <span className="text-[11px] tabular-nums text-gray-400 dark:text-gray-500">
                {readingStr}
            </span>

            {/* Readability */}
            {readability_label && (
                <>
                    <span className="text-[11px] text-gray-200 dark:text-gray-800">·</span>
                    <span className={`text-[11px] font-medium ${readabilityColor}`}>
                        {readability_label}
                    </span>
                </>
            )}

            {/* Complexity Score */}
            {meta.complexity_score && (
                <>
                    <span className="text-[11px] text-gray-200 dark:text-gray-800">·</span>
                    <span className="text-[11px] text-gray-400 dark:text-gray-500">
                        Complexity: <span className="font-medium text-gray-500 dark:text-gray-400">{meta.complexity_score}/10</span>
                    </span>
                </>
            )}

            {/* Sentiment */}
            {meta.sentiment && (
                <>
                    <span className="text-[11px] text-gray-200 dark:text-gray-800">·</span>
                    <span className="text-[11px] text-gray-400 dark:text-gray-500">
                        {meta.sentiment === "Positive" ? "😊" : meta.sentiment === "Negative" ? "😟" : "😐"} {meta.sentiment}
                    </span>
                </>
            )}
        </div>
    );
}
