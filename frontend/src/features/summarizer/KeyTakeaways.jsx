import { useState } from "react";

/**
 * KeyTakeaways — clean numbered list with left accent.
 */
export default function KeyTakeaways({ takeaways }) {
    const [expanded, setExpanded] = useState(true);

    if (!takeaways || takeaways.length === 0) return null;

    return (
        <div className="border-t border-gray-100 dark:border-gray-800/60 pt-4 mt-2">
            <button
                onClick={() => setExpanded(!expanded)}
                className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition w-full text-left mb-3"
            >
                <span className={`transition-transform duration-200 text-[10px] ${expanded ? "rotate-90" : ""}`}>
                    ▸
                </span>
                Key Takeaways
                <span className="font-normal text-gray-300 dark:text-gray-600">{takeaways.length}</span>
            </button>

            <div className={`overflow-hidden transition-all duration-300 ${expanded ? "max-h-[500px] opacity-100" : "max-h-0 opacity-0"}`}>
                <div className="border-l-2 border-gray-200 dark:border-gray-800 pl-4 space-y-2.5">
                    {takeaways.map((t, i) => (
                        <div key={i} className="flex items-start gap-2.5">
                            <span className="text-[10px] font-medium tabular-nums text-gray-300 dark:text-gray-600 pt-[3px] shrink-0 w-3 text-right">
                                {i + 1}
                            </span>
                            <p className="text-[13px] leading-relaxed text-gray-600 dark:text-gray-400">
                                {t}
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
