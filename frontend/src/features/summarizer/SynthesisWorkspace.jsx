import { useState } from "react";
import { useAppContext } from "../../contexts/AppContext.jsx";
import { synthesizeDocuments } from "../../services/api";

export default function SynthesisWorkspace() {
    const { auth } = useAppContext();
    const user = auth?.user;

    const [documentIds, setDocumentIds] = useState("");
    const [prompt, setPrompt] = useState("");
    const [loading, setLoading] = useState(false);
    const [synthesisResult, setSynthesisResult] = useState(null);
    const [error, setError] = useState(null);

    async function handleSynthesize() {
        if (!documentIds.trim()) {
            setError("Please provide at least one Document ID.");
            return;
        }
        setLoading(true);
        setError(null);
        setSynthesisResult(null);

        try {
            // Basic parse: assumes comma separated integers
            const idsArray = documentIds
                .split(",")
                .map(id => parseInt(id.trim(), 10))
                .filter(id => !isNaN(id));

            if (idsArray.length === 0) {
                throw new Error("No valid Document IDs found.");
            }

            const res = await synthesizeDocuments(idsArray, prompt.trim() || null);
            setSynthesisResult(res.summary);
        } catch (err) {
            setError(`Failed to synthesize: ${err.message}`);
        } finally {
            setLoading(false);
        }
    }

    // Auth gate: require login
    if (!user) {
        return (
            <div className="max-w-3xl mx-auto space-y-8">
                <div>
                    <h1 className="text-3xl font-semibold tracking-tight mb-3">
                        Multi-Document Synthesis
                    </h1>
                    <p className="text-gray-500 dark:text-gray-400 mb-6">
                        Compare sources and distil insights across multiple ingested documents.
                    </p>
                </div>
                <div className="bg-white dark:bg-[#121212] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm text-center">
                    <p className="text-lg font-medium mb-2">Sign in Required</p>
                    <p className="text-gray-500 dark:text-gray-400 mb-4">
                        Please sign in to use Multi-Document Synthesis.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-semibold tracking-tight mb-3">
                    Multi-Document Synthesis
                </h1>
                <p className="text-gray-500 dark:text-gray-400 mb-6">
                    Compare sources and distil insights across multiple ingested documents.
                </p>
            </div>

            <div className="bg-white dark:bg-[#121212] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                {error && <p className="mb-4 text-sm text-red-500">{error}</p>}

                <div className="space-y-4 mb-6">
                    <div>
                        <label className="block text-sm font-medium mb-2">Document IDs (Comma separated)</label>
                        <input
                            type="text"
                            value={documentIds}
                            onChange={(e) => setDocumentIds(e.target.value)}
                            placeholder="e.g. 1, 4, 7"
                            className="w-full bg-gray-50 dark:bg-[#1A1A1A] border border-gray-200 dark:border-gray-800 rounded-xl px-4 py-3 outline-none text-sm focus:border-black dark:focus:border-white transition-colors"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-2">Custom Synthesis Prompt (Optional)</label>
                        <input
                            type="text"
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            placeholder="e.g. Compare the main arguments of these authors"
                            className="w-full bg-gray-50 dark:bg-[#1A1A1A] border border-gray-200 dark:border-gray-800 rounded-xl px-4 py-3 outline-none text-sm focus:border-black dark:focus:border-white transition-colors"
                        />
                    </div>
                </div>

                <div className="flex justify-end">
                    <button
                        onClick={handleSynthesize}
                        disabled={loading || !documentIds.trim()}
                        className="px-6 py-2.5 rounded-full text-sm font-medium bg-black text-white dark:bg-white dark:text-black hover:opacity-90 disabled:opacity-50 transition"
                    >
                        {loading ? "Synthesizing..." : "Synthesize Documents"}
                    </button>
                </div>
            </div>

            {synthesisResult && (
                <div className="bg-white dark:bg-[#121212] border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                    <h3 className="text-xs uppercase tracking-wider text-gray-400 mb-6">Synthesis Result</h3>
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                        {synthesisResult.split('\n').map((line, i) => (
                            <p key={i} className="mb-2 leading-relaxed text-[#1A1A2E] dark:text-gray-200">{line}</p>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
