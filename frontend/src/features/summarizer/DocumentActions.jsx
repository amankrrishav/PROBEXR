import { useState, useEffect, useRef, useCallback } from "react";
import { generateFlashcards } from "../../services/api";
import { getBaseUrl } from "../../services/client";
import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";

// ─────────────────────────────────────────────────────────────────────────────
// Browser SpeechSynthesis TTS hook
// ─────────────────────────────────────────────────────────────────────────────
function useTTS(text) {
    const [ttsState, setTtsState] = useState("idle"); // idle | loading | speaking | paused | unsupported
    const utterRef = useRef(null);

    const isSupported = typeof window !== "undefined" && "speechSynthesis" in window;

    // Cleanup on unmount or text change
    useEffect(() => {
        return () => {
            if (utterRef.current) {
                window.speechSynthesis.cancel();
            }
        };
    }, [text]);

    const speak = useCallback(() => {
        if (!isSupported || !text) return;

        // Cancel any in-progress speech first
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterRef.current = utterance;

        // Pick a natural-sounding English voice when available
        const voices = window.speechSynthesis.getVoices();
        const preferred = voices.find(
            (v) => v.lang.startsWith("en") && (v.name.includes("Google") || v.name.includes("Samantha") || v.name.includes("Alex"))
        ) ?? voices.find((v) => v.lang.startsWith("en"));
        if (preferred) utterance.voice = preferred;

        utterance.rate = 0.95;
        utterance.pitch = 1;
        utterance.volume = 1;

        utterance.onstart = () => setTtsState("speaking");
        utterance.onpause = () => setTtsState("paused");
        utterance.onresume = () => setTtsState("speaking");
        utterance.onend = () => setTtsState("idle");
        utterance.onerror = () => setTtsState("idle");

        setTtsState("loading");
        window.speechSynthesis.speak(utterance);
    }, [isSupported, text]);

    const pause = useCallback(() => {
        window.speechSynthesis.pause();
        setTtsState("paused");
    }, []);

    const resume = useCallback(() => {
        window.speechSynthesis.resume();
        setTtsState("speaking");
    }, []);

    const stop = useCallback(() => {
        window.speechSynthesis.cancel();
        setTtsState("idle");
    }, []);

    return { ttsState, isSupported, speak, pause, resume, stop };
}

// ─────────────────────────────────────────────────────────────────────────────
// TTS button — compact pill with play / pause / stop states
// ─────────────────────────────────────────────────────────────────────────────
function TTSButton({ summaryText }) {
    const { ttsState, isSupported, speak, pause, resume, stop } = useTTS(summaryText);

    if (!isSupported) {
        return (
            <span
                className="text-[12px] font-medium px-3 py-1.5 rounded-lg text-gray-300 dark:text-gray-600 border border-dashed border-gray-200 dark:border-gray-800 cursor-default select-none"
                title="Your browser doesn't support speech synthesis"
            >
                Read Aloud — Unsupported
            </span>
        );
    }

    if (ttsState === "idle" || ttsState === "loading") {
        return (
            <button
                onClick={speak}
                disabled={ttsState === "loading" || !summaryText}
                className="text-[12px] font-medium px-3 py-1.5 rounded-lg text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-white/[0.03] transition disabled:opacity-40"
                title="Read summary aloud"
            >
                {ttsState === "loading" ? "Starting…" : "▶ Read Aloud"}
            </button>
        );
    }

    if (ttsState === "speaking") {
        return (
            <div className="flex items-center gap-1.5">
                <button
                    onClick={pause}
                    className="text-[12px] font-medium px-3 py-1.5 rounded-lg text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-white/[0.03] transition"
                    title="Pause"
                >
                    ⏸ Pause
                </button>
                <button
                    onClick={stop}
                    className="text-[12px] font-medium px-2 py-1.5 rounded-lg text-gray-400 dark:text-gray-600 hover:text-red-500 transition"
                    title="Stop"
                >
                    ✕
                </button>
            </div>
        );
    }

    if (ttsState === "paused") {
        return (
            <div className="flex items-center gap-1.5">
                <button
                    onClick={resume}
                    className="text-[12px] font-medium px-3 py-1.5 rounded-lg text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-white/[0.03] transition"
                    title="Resume"
                >
                    ▶ Resume
                </button>
                <button
                    onClick={stop}
                    className="text-[12px] font-medium px-2 py-1.5 rounded-lg text-gray-400 dark:text-gray-600 hover:text-red-500 transition"
                    title="Stop"
                >
                    ✕
                </button>
            </div>
        );
    }

    return null;
}

// ─────────────────────────────────────────────────────────────────────────────
// Main DocumentActions component
// ─────────────────────────────────────────────────────────────────────────────
export default function DocumentActions({ documentId }) {
    const { summaryText } = useSummarizerContext();
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
                {/* TTS — browser SpeechSynthesis, $0 cost */}
                <TTSButton summaryText={summaryText} />

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
