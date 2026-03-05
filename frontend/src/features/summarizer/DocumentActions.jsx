import { useState } from "react";
import { generateFlashcards } from "../../services/api";
import { getBaseUrl } from "../../services/client";

export default function DocumentActions({ documentId }) {
    const [loadingCards, setLoadingCards] = useState(false);
    const [loadingExport, setLoadingExport] = useState(false);
    const [flashcardSetId, setFlashcardSetId] = useState(null);
    const [error, setError] = useState(null);

    async function handleFlashcards() {
        if (!documentId) return;
        setLoadingCards(true);
        setError(null);
        try {
            const fcSet = await generateFlashcards(documentId, 10);
            setFlashcardSetId(fcSet.id);
        } catch {
            setError("Failed to generate flashcards");
        } finally {
            setLoadingCards(false);
        }
    }

    async function handleExportCSV() {
        if (!flashcardSetId) return;
        setLoadingExport(true);
        setError(null);
        try {
            const url = `${getBaseUrl()}/api/flashcards/${flashcardSetId}/export`;
            const res = await fetch(url, { credentials: "include" });
            if (!res.ok) throw new Error(`Export failed: ${res.status}`);
            const blob = await res.blob();
            const blobUrl = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = blobUrl;
            a.download = `flashcards_${flashcardSetId}.csv`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(blobUrl);
        } catch {
            setError("Failed to download CSV");
        } finally {
            setLoadingExport(false);
        }
    }

    return (
        <div className="border-t border-gray-100 dark:border-gray-800/60 pt-4 mt-4">
            <h3 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">
                Tools
            </h3>

            {error && <p className="text-[11px] text-red-500 mb-2">{error}</p>}

            <div className="flex items-center gap-2 flex-wrap">
                {/* TTS coming soon */}
                <span
                    className="text-[12px] font-medium px-3 py-1.5 rounded-lg text-gray-300 dark:text-gray-600 border border-dashed border-gray-200 dark:border-gray-800 cursor-default select-none"
                    title="Coming soon"
                >
                    Read Aloud — Soon
                </span>

                {!flashcardSetId ? (
                    <button
                        onClick={handleFlashcards}
                        disabled={loadingCards || !documentId}
                        className="text-[12px] font-medium px-3 py-1.5 rounded-lg text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-white/[0.03] transition disabled:opacity-40"
                    >
                        {loadingCards ? "Generating…" : "Generate Flashcards"}
                    </button>
                ) : (
                    <div className="flex items-center gap-2">
                        <span className="text-[12px] text-emerald-600 dark:text-emerald-400 font-medium">
                            Flashcards ready
                        </span>
                        <button
                            onClick={handleExportCSV}
                            disabled={loadingExport}
                            className="text-[12px] font-medium px-3 py-1.5 rounded-lg text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-white/[0.03] transition disabled:opacity-40"
                        >
                            {loadingExport ? "Downloading…" : "Download CSV"}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
