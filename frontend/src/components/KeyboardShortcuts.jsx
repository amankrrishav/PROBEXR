/**
 * KeyboardShortcuts — Beautiful modal showing all keyboard shortcuts.
 * Triggered by ⌘/ (or Ctrl/ on Windows).
 */
export default function KeyboardShortcuts({ open, onClose }) {
  if (!open) return null;

  const isMac = typeof navigator !== "undefined" && /Mac/i.test(navigator.userAgent);
  const mod = isMac ? "⌘" : "Ctrl";

  const shortcuts = [
    { keys: [mod, "Enter"], action: "Summarize" },
    { keys: [mod, "F"], action: "Focus mode" },
    { keys: [mod, "K"], action: "New summary" },
    { keys: [mod, "/"], action: "Keyboard shortcuts" },
    { keys: [mod, "Shift", "C"], action: "Clear input" },
    { keys: ["Esc"], action: "Exit modal / Focus mode" },
  ];

  return (
    <div className="shortcuts-overlay" onClick={onClose}>
      <div className="shortcuts-modal" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between" style={{ marginBottom: 24 }}>
          <h2 className="font-display" style={{ fontSize: 22, color: "var(--ink-primary)" }}>
            Keyboard Shortcuts
          </h2>
          <button
            onClick={onClose}
            className="btn-ghost"
            style={{ fontSize: 16, padding: "4px 8px" }}
          >
            ×
          </button>
        </div>

        <div>
          {shortcuts.map((s, i) => (
            <div key={i} className="shortcut-row">
              <span className="font-body" style={{ fontSize: 13, color: "var(--ink-secondary)" }}>
                {s.action}
              </span>
              <div className="shortcut-keys">
                {s.keys.map((k, j) => (
                  <span key={j} className="shortcut-key">{k}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
