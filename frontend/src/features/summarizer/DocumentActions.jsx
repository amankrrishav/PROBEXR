import { useState, useEffect, useRef, useCallback } from "react";
import { generateFlashcards } from "../../services/api";
import { getBaseUrl } from "../../services/client";
import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";

// ─── Browser SpeechSynthesis TTS ──────────────────────────────────────
function useTTS(text) {
    const [ttsState, setTtsState] = useState("idle");
    const utterRef = useRef(null);
    const isSupported = typeof window !== "undefined" && "speechSynthesis" in window;

    useEffect(() => {
        return () => { if (utterRef.current) window.speechSynthesis.cancel(); };
    }, [text]);

    const speak = useCallback(() => {
        if (!isSupported || !text) return;
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterRef.current = utterance;
        const voices = window.speechSynthesis.getVoices();
        const preferred = voices.find(v => v.lang.startsWith("en") && (v.name.includes("Google") || v.name.includes("Samantha")))
            ?? voices.find(v => v.lang.startsWith("en"));
        if (preferred) utterance.voice = preferred;
        utterance.rate = 0.95;
        utterance.onstart = () => setTtsState("speaking");
        utterance.onpause = () => setTtsState("paused");
        utterance.onresume = () => setTtsState("speaking");
        utterance.onend = () => setTtsState("idle");
        utterance.onerror = () => setTtsState("idle");
        setTtsState("loading");
        window.speechSynthesis.speak(utterance);
    }, [isSupported, text]);

    const pause = useCallback(() => { window.speechSynthesis.pause(); setTtsState("paused"); }, []);
    const resume = useCallback(() => { window.speechSynthesis.resume(); setTtsState("speaking"); }, []);
    const stop = useCallback(() => { window.speechSynthesis.cancel(); setTtsState("idle"); }, []);

    return { ttsState, isSupported, speak, pause, resume, stop };
}

function TTSButton({ summaryText }) {
    const { ttsState, isSupported, speak, pause, resume, stop } = useTTS(summaryText);

    if (!isSupported) {
        return <span className="chip" style={{ opacity: 0.5 }}>Read Aloud — Unsupported</span>;
    }

    if (ttsState === "idle" || ttsState === "loading") {
        return (
            <button onClick={speak} disabled={ttsState === "loading" || !summaryText}
                className="btn-ghost" style={{ fontSize: 12 }}>
                {ttsState === "loading" ? "Starting…" : "▶ Read Aloud"}
            </button>
        );
    }

    if (ttsState === "speaking") {
        return (
            <div className="flex items-center gap-1">
                <button onClick={pause} className="btn-ghost" style={{ fontSize: 12 }}>⏸ Pause</button>
                <button onClick={stop} className="btn-ghost" style={{ fontSize: 12, color: "var(--accent-warn)" }}>✕</button>
            </div>
        );
    }

    if (ttsState === "paused") {
        return (
            <div className="flex items-center gap-1">
                <button onClick={resume} className="btn-ghost" style={{ fontSize: 12 }}>▶ Resume</button>
                <button onClick={stop} className="btn-ghost" style={{ fontSize: 12, color: "var(--accent-warn)" }}>✕</button>
            </div>
        );
    }
    return null;
}

// ─── DocumentActions ─────────────────────────────────────────────────
export default function DocumentActions({ documentId }) {
    const { summaryText } = useSummarizerContext();
    const [loadingCards, setLoadingCards] = useState(false);
    const [loadingExport, setLoadingExport] = useState(false);
    const [flashcardSetId, setFlashcardSetId] = useState(null);
    const [error, setError] = useState(null);

    async function handleFlashcards() {
        if (!documentId) return;
        setLoadingCards(true); setError(null);
        try { const fcSet = await generateFlashcards(documentId, 10); setFlashcardSetId(fcSet.id); }
        catch { setError("Failed to generate flashcards"); }
        finally { setLoadingCards(false); }
    }

    async function handleExportCSV() {
        if (!flashcardSetId) return;
        setLoadingExport(true); setError(null);
        try {
            const url = `${getBaseUrl()}/api/flashcards/${flashcardSetId}/export`;
            const res = await fetch(url, { credentials: "include" });
            if (!res.ok) throw new Error(`Export failed: ${res.status}`);
            const blob = await res.blob();
            const blobUrl = URL.createObjectURL(blob);
            const a = document.createElement("a"); a.href = blobUrl;
            a.download = `flashcards_${flashcardSetId}.csv`;
            document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(blobUrl);
        } catch { setError("Failed to download CSV"); }
        finally { setLoadingExport(false); }
    }

    return (
        <div style={{ borderTop: "1px solid var(--border)", paddingTop: 16, marginTop: 16 }}>
            <p className="section-header" style={{ marginBottom: 12 }}>Tools</p>

            {error && (
                <p className="font-body" style={{ fontSize: 11, color: "var(--accent-warn)", marginBottom: 8 }}>{error}</p>
            )}

            <div className="flex items-center gap-2 flex-wrap">
                <TTSButton summaryText={summaryText} />

                {!flashcardSetId ? (
                    <button onClick={handleFlashcards} disabled={loadingCards || !documentId}
                        className="btn-ghost" style={{ fontSize: 12 }}>
                        {loadingCards ? "Generating…" : "⬜ Flashcards"}
                    </button>
                ) : (
                    <div className="flex items-center gap-2">
                        <span className="chip chip-teal" style={{ fontSize: 11 }}>Flashcards ready</span>
                        <button onClick={handleExportCSV} disabled={loadingExport}
                            className="btn-ghost" style={{ fontSize: 12 }}>
                            {loadingExport ? "Downloading…" : "⬇ Download CSV"}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
