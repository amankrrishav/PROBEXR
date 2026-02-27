import { useState } from "react";
import { generateFlashcards, generateAudioSummary } from "../../services/api";

export default function DocumentActions({ documentId }) {
    const [loadingAudio, setLoadingAudio] = useState(false);
    const [loadingCards, setLoadingCards] = useState(false);
    const [audioUrl, setAudioUrl] = useState(null);
    const [flashcardSetId, setFlashcardSetId] = useState(null);
    const [error, setError] = useState(null);

    async function handleTTS() {
        if (!documentId) return;
        setLoadingAudio(true);
        setError(null);
        try {
            const summary = await generateAudioSummary(documentId);
            setAudioUrl(summary.audio_url);
        } catch (err) {
            setError("Failed to generate audio summary");
        } finally {
            setLoadingAudio(false);
        }
    }

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

    return (
        <div className="flex flex-col gap-4 border-t border-gray-200 dark:border-gray-800 pt-6 mt-6">
            <h3 className="text-xs uppercase tracking-wider text-gray-400">
                Review Tools
            </h3>

            {error && <p className="text-xs text-red-500">{error}</p>}

            <div className="flex gap-4">
                {!audioUrl ? (
                    <button
                        onClick={handleTTS}
                        disabled={loadingAudio || !documentId}
                        className="text-sm font-medium px-4 py-2 bg-gray-100 dark:bg-[#1A1A1A] text-black dark:text-white rounded-lg hover:opacity-80 transition-opacity disabled:opacity-50"
                    >
                        {loadingAudio ? "Generating Audio..." : "Read Aloud"}
                    </button>
                ) : (
                    <div className="flex items-center gap-3">
                        <span className="text-sm text-green-600 dark:text-green-400">Audio Ready:</span>
                        <a href={audioUrl} target="_blank" rel="noreferrer" className="text-sm underline hover:text-gray-500">Listen</a>
                    </div>
                )}

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
                        <a href={`/api/flashcards/${flashcardSetId}/export`} target="_blank" rel="noreferrer" className="text-sm underline hover:text-gray-500">Download CSV</a>
                    </div>
                )}
            </div>
        </div>
    );
}
