import { useEffect, useState } from "react";

/**
 * SummaryStats — animated pill-badges showing compression stats.
 * Appears above the summary text with a stagger animation.
 */
export default function SummaryStats({ meta }) {
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        if (meta) {
            const t = setTimeout(() => setVisible(true), 200);
            return () => clearTimeout(t);
        }
        setVisible(false);
    }, [meta]);

    if (!meta) return null;

    const { original_word_count, summary_word_count, compression_ratio, reading_time_seconds } = meta;

    const readingStr = reading_time_seconds < 60
        ? `${reading_time_seconds}s read`
        : `${Math.round(reading_time_seconds / 60)} min read`;

    const stats = [
        {
            icon: "📊",
            label: `${original_word_count?.toLocaleString()} → ${summary_word_count?.toLocaleString()} words`,
        },
        {
            icon: "⚡",
            label: `${compression_ratio}% compressed`,
        },
        {
            icon: "⏱️",
            label: readingStr,
        },
    ];

    return (
        <div className={`flex flex-wrap gap-2 mb-5 transition-all duration-500 ${visible ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-2"}`}>
            {stats.map((s, i) => (
                <span
                    key={i}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300"
                    style={{ transitionDelay: `${i * 100}ms` }}
                >
                    <span>{s.icon}</span>
                    {s.label}
                </span>
            ))}
        </div>
    );
}
