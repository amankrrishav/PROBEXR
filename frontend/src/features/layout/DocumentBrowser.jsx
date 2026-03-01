import { useState, useEffect, useCallback } from "react";
import { useAppContext } from "../../contexts/AppContext.jsx";
import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";
import { getDocuments, deleteDocument } from "../../services/api";

export default function DocumentBrowser({ onSelectDocument }) {
    const { auth } = useAppContext();
    const summarizer = useSummarizerContext();
    const user = auth?.user;

    const [documents, setDocuments] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [pages, setPages] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [deletingId, setDeletingId] = useState(null);

    const fetchDocuments = useCallback(async (p = 1) => {
        setLoading(true);
        setError(null);
        try {
            const res = await getDocuments(p, 10);
            setDocuments(res.documents);
            setTotal(res.total);
            setPage(res.page);
            setPages(res.pages);
        } catch (err) {
            setError(err.message || "Failed to load documents");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (user) {
            fetchDocuments(1);
        }
    }, [user, fetchDocuments]);

    async function handleDelete(docId) {
        if (!window.confirm("Delete this document? This cannot be undone.")) return;
        setDeletingId(docId);
        try {
            await deleteDocument(docId);
            // Refresh list
            await fetchDocuments(page);
        } catch (err) {
            setError("Failed to delete document");
        } finally {
            setDeletingId(null);
        }
    }

    function handleSelectForSummarize(doc) {
        // Load the document content into the summarizer
        if (onSelectDocument) {
            onSelectDocument(doc);
        }
    }

    if (!user) {
        return (
            <div className="px-2 py-3 text-xs text-gray-400 dark:text-gray-500 italic">
                Sign in to see your documents.
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between px-2">
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Documents ({total})
                </span>
                <button
                    onClick={() => fetchDocuments(page)}
                    disabled={loading}
                    className="text-[10px] text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition"
                    title="Refresh"
                >
                    {loading ? "…" : "↻"}
                </button>
            </div>

            {error && (
                <p className="px-2 text-[11px] text-red-500">{error}</p>
            )}

            {documents.length === 0 && !loading ? (
                <p className="px-2 py-2 text-xs text-gray-400 dark:text-gray-500 italic">
                    No documents yet. Summarize a URL or paste text to get started.
                </p>
            ) : (
                <div className="flex flex-col gap-1 max-h-[280px] overflow-y-auto">
                    {documents.map((doc) => (
                        <div
                            key={doc.id}
                            className="group flex items-start gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition cursor-pointer"
                            onClick={() => handleSelectForSummarize(doc)}
                        >
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate text-gray-800 dark:text-gray-200">
                                    {doc.title || "Untitled"}
                                </p>
                                <p className="text-[10px] text-gray-400 dark:text-gray-500 truncate">
                                    {doc.word_count} words · {doc.url === "pasted_text" ? "Pasted" : new URL(doc.url).hostname}
                                </p>
                            </div>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleDelete(doc.id);
                                }}
                                disabled={deletingId === doc.id}
                                className="opacity-0 group-hover:opacity-100 text-[10px] text-red-400 hover:text-red-600 dark:text-red-500 dark:hover:text-red-300 transition-opacity px-1"
                                title="Delete document"
                            >
                                {deletingId === doc.id ? "…" : "✕"}
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* Pagination */}
            {pages > 1 && (
                <div className="flex items-center justify-center gap-2 px-2 pt-1">
                    <button
                        onClick={() => fetchDocuments(page - 1)}
                        disabled={page <= 1 || loading}
                        className="text-[10px] px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 disabled:opacity-40 transition"
                    >
                        ← Prev
                    </button>
                    <span className="text-[10px] text-gray-400">
                        {page} / {pages}
                    </span>
                    <button
                        onClick={() => fetchDocuments(page + 1)}
                        disabled={page >= pages || loading}
                        className="text-[10px] px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 disabled:opacity-40 transition"
                    >
                        Next →
                    </button>
                </div>
            )}
        </div>
    );
}
