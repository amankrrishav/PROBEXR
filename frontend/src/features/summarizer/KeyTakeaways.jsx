import { useState } from "react";

/**
 * KeyTakeaways — collapsible bullet-point section showing the key takeaways
 * from the summarized content. Appears after the summary prose.
 */
export default function KeyTakeaways({ takeaways }) {
    const [expanded, setExpanded] = useState(true);

    if (!takeaways || takeaways.length === 0) return null;

    return (
        <div className="border-t border-gray-200 dark:border-gray-800 pt-5 mt-5">
            <button
                onClick={() => setExpanded(!expanded)}
                className="flex items-center gap-2 text-xs uppercase tracking-wider text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors w-full text-left"
            >
                <span className={`transition-transform duration-200 ${expanded ? "rotate-90" : ""}`}>
                    ▸
                </span>
                Key Takeaways ({takeaways.length})
            </button>

            <div className={`overflow-hidden transition-all duration-300 ${expanded ? "max-h-96 opacity-100 mt-3" : "max-h-0 opacity-0"}`}>
                <ul className="space-y-2">
                    {takeaways.map((t, i) => (
                        <li
                            key={i}
                            className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300"
                        >
                            <span className="text-gray-400 dark:text-gray-500 mt-0.5 text-xs">•</span>
                            <span className="leading-relaxed">{t}</span>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}
