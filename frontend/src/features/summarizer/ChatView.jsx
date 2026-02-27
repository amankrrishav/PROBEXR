import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "../../services/api";

export default function ChatView({ documentId }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [sessionId, setSessionId] = useState(null);
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    async function handleSend(e) {
        if (e) e.preventDefault();
        if (!input.trim() || loading || !documentId) return;

        const userMessage = input.trim();
        setInput("");
        setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
        setLoading(true);

        try {
            const response = await sendChatMessage(documentId, userMessage, sessionId);
            setSessionId(response.session_id);
            setMessages((prev) => [...prev, { role: "assistant", content: response.content }]);
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: `Error: ${err.message}` },
            ]);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="mt-8 border-t border-gray-200 dark:border-gray-800 pt-6">
            <h3 className="text-xs uppercase tracking-wider text-gray-400 mb-4">
                Ask questions about this text
            </h3>

            <div className="flex flex-col space-y-4 max-h-64 overflow-y-auto mb-4 pr-2">
                {messages.length === 0 ? (
                    <p className="text-sm text-gray-500 italic">No messages yet. Send a question below!</p>
                ) : (
                    messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`p-3 rounded-xl text-sm max-w-[85%] ${msg.role === "user"
                                    ? "bg-gray-100 dark:bg-[#1A1A1A] text-black dark:text-white self-end ml-auto"
                                    : "bg-black dark:bg-white text-white dark:text-black self-start"
                                }`}
                        >
                            {msg.content}
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSend} className="flex gap-2 relative">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask a question..."
                    className="flex-1 bg-gray-50 dark:bg-[#1A1A1A] border border-gray-200 dark:border-gray-800 rounded-full px-4 py-2 text-sm outline-none w-full"
                    disabled={loading || !documentId}
                />
                <button
                    type="submit"
                    disabled={loading || !input.trim() || !documentId}
                    className="bg-black dark:bg-white text-white dark:text-black px-4 py-2 rounded-full text-sm font-medium disabled:opacity-50"
                >
                    {loading ? "..." : "Send"}
                </button>
            </form>
        </div>
    );
}
