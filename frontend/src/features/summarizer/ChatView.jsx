import { useState, useRef, useEffect } from "react";
import { sendChatMessage, sendChatMessageStream } from "../../services/api";

export default function ChatView({ documentId }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [sessionId, setSessionId] = useState(null);
    const [loading, setLoading] = useState(false);
    const [streaming, setStreaming] = useState(false);
    const [streamingContent, setStreamingContent] = useState("");
    const messagesEndRef = useRef(null);
    const abortRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => { scrollToBottom(); }, [messages, streamingContent]);

    function cancelChatStream() {
        if (abortRef.current) { abortRef.current.abort(); abortRef.current = null; }
        if (streamingContent) {
            setMessages((prev) => [...prev, { role: "assistant", content: streamingContent + " [stopped]" }]);
        }
        setStreaming(false);
        setStreamingContent("");
        setLoading(false);
    }

    async function handleSend(e) {
        if (e) e.preventDefault();
        if (!input.trim() || loading || streaming || !documentId) return;

        const userMessage = input.trim();
        setInput("");
        setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
        setLoading(true);

        // Streaming first
        const controller = new AbortController();
        abortRef.current = controller;
        setStreaming(true);
        setLoading(false);
        let streamedContent = "";
        let streamSucceeded = false;

        try {
            await sendChatMessageStream(
                documentId, userMessage, sessionId,
                (token) => { streamedContent += token; setStreamingContent(streamedContent); },
                (metadata) => {
                    streamSucceeded = true;
                    if (metadata.session_id) setSessionId(metadata.session_id);
                    setMessages((prev) => [...prev, { role: "assistant", content: streamedContent }]);
                    setStreamingContent(""); setStreaming(false); abortRef.current = null;
                },
                (errMsg) => { console.warn("Chat streaming failed:", errMsg); },
                controller,
            );
            if (streamSucceeded) return;
        } catch { /* fall through */ }

        // Fallback
        setStreaming(false); setStreamingContent(""); setLoading(true); abortRef.current = null;
        try {
            const response = await sendChatMessage(documentId, userMessage, sessionId);
            setSessionId(response.session_id);
            setMessages((prev) => [...prev, { role: "assistant", content: response.content }]);
        } catch (err) {
            setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${err.message}` }]);
        } finally {
            setLoading(false);
        }
    }

    const isBusy = loading || streaming;

    return (
        <div className="border-t border-gray-100 dark:border-gray-800/60 pt-4 mt-4">
            <h3 className="text-[11px] font-semibold uppercase tracking-widest text-gray-400 dark:text-gray-500 mb-3">
                Ask about this text
            </h3>

            {/* Messages */}
            <div className="flex flex-col gap-2.5 max-h-[280px] overflow-y-auto mb-3 pr-1">
                {messages.length === 0 && !streaming ? (
                    <p className="text-[12px] text-gray-400 dark:text-gray-500 italic py-2">
                        Ask a question about the document…
                    </p>
                ) : (
                    <>
                        {messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className={`px-3.5 py-2.5 rounded-xl text-[13px] leading-relaxed max-w-[85%] ${msg.role === "user"
                                    ? "bg-gray-100 dark:bg-gray-800/60 text-gray-800 dark:text-gray-200 self-end ml-auto"
                                    : "bg-gray-900 dark:bg-white text-white dark:text-gray-900 self-start"
                                    }`}
                            >
                                {msg.content}
                            </div>
                        ))}
                        {streaming && streamingContent && (
                            <div className="px-3.5 py-2.5 rounded-xl text-[13px] leading-relaxed max-w-[85%] bg-gray-900 dark:bg-white text-white dark:text-gray-900 self-start">
                                {streamingContent}
                                <span className="inline-block w-[5px] h-[14px] bg-gray-400 dark:bg-gray-600 animate-pulse ml-0.5 align-text-bottom rounded-sm" />
                            </div>
                        )}
                    </>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSend} className="flex gap-2">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Type a question…"
                    className="flex-1 bg-gray-50 dark:bg-gray-800/40 border border-gray-200/80 dark:border-gray-800/80 rounded-xl px-3.5 py-2 text-[13px] outline-none placeholder:text-gray-300 dark:placeholder:text-gray-600 focus:border-gray-400 dark:focus:border-gray-600 transition"
                    disabled={isBusy || !documentId}
                />
                {streaming ? (
                    <button
                        type="button"
                        onClick={cancelChatStream}
                        className="text-[12px] font-medium px-3 py-2 rounded-xl text-red-500 border border-red-200 dark:border-red-800/40 hover:bg-red-50 dark:hover:bg-red-900/20 transition"
                    >
                        Stop
                    </button>
                ) : (
                    <button
                        type="submit"
                        disabled={loading || !input.trim() || !documentId}
                        className="text-[12px] font-medium px-4 py-2 rounded-xl bg-gray-900 dark:bg-white text-white dark:text-black disabled:opacity-30 hover:opacity-90 transition"
                    >
                        {loading ? "…" : "Send"}
                    </button>
                )}
            </form>
        </div>
    );
}
