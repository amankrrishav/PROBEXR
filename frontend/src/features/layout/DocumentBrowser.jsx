import { useState, useEffect, useCallback } from "react";
import { useAppContext } from "../../contexts/AppContext.jsx";
import { getDocuments, deleteDocument } from "../../services/api";

// ─── Helpers ─────────────────────────────────────────────────────────
function relativeTime(isoStr) {
    if (!isoStr) return "";
    const diff = Date.now() - new Date(isoStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    if (days < 7) return `${days}d ago`;
    if (days < 30) return `${Math.floor(days / 7)}w ago`;
    return new Date(isoStr).toLocaleDateString("en", { month: "short", day: "numeric" });
}

function sourceBadge(url) {
    if (!url || url === "pasted_text") return { label: "Pasted", color: "bg-violet-100 text-violet-600 dark:bg-violet-900/30 dark:text-violet-400" };
    try {
        let host = new URL(url).hostname;
        if (host.startsWith("www.")) host = host.slice(4);
        return { label: host, color: "bg-sky-100 text-sky-600 dark:bg-sky-900/30 dark:text-sky-400" };
    } catch {
        return { label: "Web", color: "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400" };
    }
}

// ─── Document Card ───────────────────────────────────────────────────
function DocCard({ doc, onDelete, deleting }) {
    const badge = sourceBadge(doc.url);

    return (
        <div className="group relative px-3 py-2.5 rounded-xl hover:bg-gray-50 dark:hover:bg-white/[0.03] transition-colors cursor-pointer">
            {/* Title */}
            <p className="text-[13px] font-medium leading-snug text-gray-800 dark:text-gray-200 pr-5 line-clamp-2 mb-1">
                {doc.title || "Untitled"}
            </p>

            {/* Meta row */}
            <div className="flex items-center gap-1.5 flex-wrap">
                <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium ${badge.color}`}>
                    {badge.label}
                </span>
                <span className="text-[10px] text-gray-400 dark:text-gray-500">
                    {doc.word_count?.toLocaleString()} words
                </span>
                <span className="text-[10px] text-gray-300 dark:text-gray-700">·</span>
                <span className="text-[10px] text-gray-400 dark:text-gray-500">
                    {relativeTime(doc.created_at)}
                </span>
            </div>

            {/* Delete button — appears on hover */}
            <button
                onClick={(e) => { e.stopPropagation(); onDelete(doc.id); }}
                disabled={deleting}
                className="absolute top-2.5 right-2 opacity-0 group-hover:opacity-100 w-5 h-5 flex items-center justify-center rounded-md text-[10px] text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 dark:hover:text-red-400 transition-all"
                title="Delete"
            >
                {deleting ? "…" : "✕"}
            </button>
        </div>
    );
}

// ═════════════════════════════════════════════════════════════════════
// DOCUMENT BROWSER
// ═════════════════════════════════════════════════════════════════════
export default function DocumentBrowser({ onSelectDocument }) {
    const { auth } = useAppContext();
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
        if (user) fetchDocuments(1);
    }, [user, fetchDocuments]);

    async function handleDelete(docId) {
        if (!window.confirm("Delete this document? This cannot be undone.")) return;
        setDeletingId(docId);
        try {
            await deleteDocument(docId);
            await fetchDocuments(page);
        } catch {
            setError("Failed to delete document");
        } finally {
            setDeletingId(null);
        }
    }

    function handleSelect(doc) {
        if (onSelectDocument) onSelectDocument(doc);
    }

    /* ── Not signed in ── */
    if (!user) {
        return (
            <div className="px-2 py-6 text-center">
                <div className="text-2xl mb-2 opacity-40">📂</div>
                <p className="text-[11px] text-gray-400 dark:text-gray-500">
                    Sign in to see your library
                </p>
            </div>
        );
    }

    /* ── Main ── */
    return (
        <div className="flex flex-col gap-1">
            {/* Header */}
            <div className="flex items-center justify-between px-3 mb-1">
                <span className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-widest">
                    Library{total > 0 ? ` · ${total}` : ""}
                </span>
                <button
                    onClick={() => fetchDocuments(page)}
                    disabled={loading}
                    className="text-[10px] text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition w-5 h-5 flex items-center justify-center rounded hover:bg-gray-100 dark:hover:bg-gray-800"
                    title="Refresh"
                >
                    {loading ? "…" : "↻"}
                </button>
            </div>

            {error && (
                <p className="px-3 text-[11px] text-red-500 mb-1">{error}</p>
            )}

            {documents.length === 0 && !loading ? (
                <div className="px-3 py-6 text-center">
                    <div className="text-xl mb-2 opacity-30">📄</div>
                    <p className="text-[11px] text-gray-400 dark:text-gray-500 leading-relaxed">
                        No documents yet.<br />
                        Summarize an article to start building your library.
                    </p>
                </div>
            ) : (
                <div className="flex flex-col gap-0.5 max-h-[320px] overflow-y-auto pr-0.5 scrollbar-thin">
                    {documents.map((doc) => (
                        <div key={doc.id} onClick={() => handleSelect(doc)}>
                            <DocCard
                                doc={doc}
                                onDelete={handleDelete}
                                deleting={deletingId === doc.id}
                            />
                        </div>
                    ))}
                </div>
            )}

            {/* Pagination */}
            {pages > 1 && (
                <div className="flex items-center justify-center gap-3 px-2 pt-2 mt-1 border-t border-gray-100 dark:border-gray-800/50">
                    <button
                        onClick={() => fetchDocuments(page - 1)}
                        disabled={page <= 1 || loading}
                        className="text-[10px] text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-30 transition"
                    >
                        ← Prev
                    </button>
                    <span className="text-[10px] text-gray-400 tabular-nums">
                        {page} / {pages}
                    </span>
                    <button
                        onClick={() => fetchDocuments(page + 1)}
                        disabled={page >= pages || loading}
                        className="text-[10px] text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-30 transition"
                    >
                        Next →
                    </button>
                </div>
            )}
        </div>
    );
}
