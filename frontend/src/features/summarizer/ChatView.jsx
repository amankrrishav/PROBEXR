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

    const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    useEffect(() => { scrollToBottom(); }, [messages, streamingContent]);

    function cancelChatStream() {
        if (abortRef.current) { abortRef.current.abort(); abortRef.current = null; }
        if (streamingContent) {
            setMessages((prev) => [...prev, { role: "assistant", content: streamingContent + " [stopped]" }]);
        }
        setStreaming(false); setStreamingContent(""); setLoading(false);
    }

    async function handleSend(e) {
        if (e) e.preventDefault();
        if (!input.trim() || loading || streaming || !documentId) return;

        const userMessage = input.trim();
        setInput(""); setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
        setLoading(true);

        const controller = new AbortController();
        abortRef.current = controller;
        setStreaming(true); setLoading(false);
        let streamedContent = ""; let streamSucceeded = false;

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

        setStreaming(false); setStreamingContent(""); setLoading(true); abortRef.current = null;
        try {
            const response = await sendChatMessage(documentId, userMessage, sessionId);
            setSessionId(response.session_id);
            setMessages((prev) => [...prev, { role: "assistant", content: response.content }]);
        } catch (err) {
            setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${err.message}` }]);
        } finally { setLoading(false); }
    }

    const isBusy = loading || streaming;

    return (
        <div style={{ borderTop: "1px solid var(--border-dim)", paddingTop: 16, marginTop: 16 }}>
            <p className="section-header" style={{ marginBottom: 12 }}>Ask about this text</p>

            {/* Messages */}
            <div className="flex flex-col gap-2" style={{ maxHeight: 280, overflowY: "auto", marginBottom: 12 }}>
                {messages.length === 0 && !streaming ? (
                    <p className="font-body" style={{ fontSize: 12, color: "var(--ink-tertiary)", fontStyle: "italic", padding: "8px 0" }}>
                        Ask a question about the document…
                    </p>
                ) : (
                    <>
                        {messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className="font-body"
                                style={{
                                    padding: "10px 14px", borderRadius: 12, fontSize: 13, lineHeight: 1.6,
                                    maxWidth: "85%",
                                    ...(msg.role === "user"
                                        ? { background: "var(--bg-elevated)", color: "var(--ink-primary)", alignSelf: "flex-end", marginLeft: "auto" }
                                        : { background: "var(--amber)", color: "#0B0906", alignSelf: "flex-start" }
                                    ),
                                }}
                            >
                                {msg.content}
                            </div>
                        ))}
                        {streaming && streamingContent && (
                            <div className="font-body" style={{
                                padding: "10px 14px", borderRadius: 12, fontSize: 13, lineHeight: 1.6,
                                maxWidth: "85%", background: "var(--amber)", color: "#0B0906", alignSelf: "flex-start",
                            }}>
                                {streamingContent}
                                <span style={{
                                    display: "inline-block", width: 5, height: 14, marginLeft: 2,
                                    background: "rgba(11,9,6,0.4)", borderRadius: 1,
                                    animation: "amberPulseDot 1s infinite", verticalAlign: "text-bottom",
                                }} />
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
                    className="font-body"
                    style={{
                        flex: 1, background: "var(--bg-input)", border: "1px solid var(--border-dim)",
                        borderRadius: "var(--radius-input)", padding: "10px 14px",
                        fontSize: 13, color: "var(--ink-primary)", outline: "none",
                        transition: "border-color var(--dur-base) var(--ease)",
                    }}
                    onFocus={(e) => e.target.style.borderColor = "var(--border-lit)"}
                    onBlur={(e) => e.target.style.borderColor = "var(--border-dim)"}
                    disabled={isBusy || !documentId}
                />
                {streaming ? (
                    <button type="button" onClick={cancelChatStream} className="btn-ghost" style={{ color: "var(--rose)" }}>
                        Stop
                    </button>
                ) : (
                    <button
                        type="submit"
                        disabled={loading || !input.trim() || !documentId}
                        className="btn-primary"
                        style={{ padding: "10px 20px" }}
                    >
                        {loading ? "…" : "Send"}
                    </button>
                )}
            </form>
        </div>
    );
}
