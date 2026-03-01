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
        } catch (err) {
            setError("Failed to generate flashcards");
        } finally {
            setLoadingCards(false);
        }
    }

    /**
     * Download the flashcard CSV with credentials included.
     * A bare <a href> does NOT send cookies — this fetch approach does.
     */
    async function handleExportCSV() {
        if (!flashcardSetId) return;
        setLoadingExport(true);
        setError(null);
        try {
            const url = `${getBaseUrl()}/api/flashcards/${flashcardSetId}/export`;
            const res = await fetch(url, { credentials: "include" });
            if (!res.ok) {
                throw new Error(`Export failed: ${res.status} ${res.statusText}`);
            }
            const blob = await res.blob();
            const blobUrl = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = blobUrl;
            a.download = `flashcards_${flashcardSetId}.csv`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(blobUrl);
        } catch (err) {
            setError("Failed to download CSV. Please try again.");
        } finally {
            setLoadingExport(false);
        }
    }

    return (
        <div className="flex flex-col gap-4 border-t border-gray-200 dark:border-gray-800 pt-6 mt-6">
            <h3 className="text-xs uppercase tracking-wider text-gray-400">
                Review Tools
            </h3>

            {error && <p className="text-xs text-red-500">{error}</p>}

            <div className="flex gap-4 flex-wrap">
                {/* TTS: Coming Soon */}
                <span
                    className="text-sm font-medium px-4 py-2 bg-gray-50 dark:bg-[#1A1A1A] text-gray-400 dark:text-gray-500 rounded-lg border border-dashed border-gray-300 dark:border-gray-700 cursor-default select-none"
                    title="Text-to-Speech is coming soon"
                >
                    🔊 Read Aloud — Coming Soon
                </span>

                {!flashcardSetId ? (
                    <button
                        onClick={handleFlashcards}
                        disabled={loadingCards || !documentId}
                        className="text-sm font-medium px-4 py-2 bg-gray-100 dark:bg-[#1A1A1A] text-black dark:text-white rounded-lg hover:opacity-80 transition-opacity disabled:opacity-50"
                    >
                        {loadingCards ? "Creating Flashcards..." : "Generate Flashcards"}
                    </button>
                ) : (
                    <div className="flex items-center gap-3">
                        <span className="text-sm text-green-600 dark:text-green-400">Flashcards Ready:</span>
                        <button
                            onClick={handleExportCSV}
                            disabled={loadingExport}
                            className="text-sm underline hover:text-gray-500 disabled:opacity-50 bg-transparent border-none cursor-pointer"
                        >
                            {loadingExport ? "Downloading..." : "Download CSV"}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
