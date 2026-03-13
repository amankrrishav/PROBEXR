import { useState } from "react";
import { useAppContext } from "../../contexts/AppContext.jsx";
import { useSummarizerContext } from "../../contexts/SummarizerContext.jsx";
import { AccountSettings } from "../auth";

const NAV_ITEMS = [
  { id: "summarize",  icon: "✦", label: "Single Document" },
  { id: "synthesize", icon: "⊞", label: "Multi-Doc Synthesis" },
  { id: "analytics",  icon: "◈", label: "Analytics" },
];

export default function Sidebar({ appName, onOpenAuth, onLogout, activeTab, setActiveTab }) {
  const { dark, toggleTheme, backendMode, auth } = useAppContext();
  const { user } = auth;
  const { reset, history, restoreFromHistory } = useSummarizerContext();
  const [accountOpen, setAccountOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);

  const initial = user?.full_name
    ? user.full_name.charAt(0).toUpperCase()
    : user?.email
      ? user.email.charAt(0).toUpperCase()
      : null;

  function formatTime(timestamp) {
    if (!timestamp) return "";
    const now = Date.now();
    const t = new Date(timestamp).getTime();
    const diff = Math.floor((now - t) / 1000);
    if (diff < 60) return "now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
    return `${Math.floor(diff / 86400)}d`;
  }

  const sidebarContent = (
    <div className="flex flex-col h-full" style={{
      background: "var(--bg-surface)",
      borderRight: "1px solid var(--border-dim)",
      width: 248,
    }}>
      <AccountSettings open={settingsOpen} onClose={() => setSettingsOpen(false)} />

      {/* ── Brand ── */}
      <div style={{ padding: "24px 24px 16px" }}>
        <h1 className="font-body" style={{
          fontSize: 18, fontWeight: 700, color: "var(--ink-primary)",
          letterSpacing: "-0.01em",
        }}>
          {appName ?? "PROBEXR"}
        </h1>
        {backendMode && (
          <div className="flex items-center gap-2" style={{ marginTop: 8 }}>
            <div className="pulse-dot live" />
            <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-tertiary)" }}>
              Live · {backendMode}
            </span>
          </div>
        )}
      </div>

      {/* ── New Summary CTA ── */}
      <div style={{ padding: "0 16px 16px" }}>
        <button
          onClick={() => { setActiveTab("summarize"); reset(); setMobileOpen(false); }}
          className="btn-primary w-full"
          style={{ height: 44, fontSize: 14 }}
        >
          <span>✦</span>
          New Summary
        </button>
      </div>

      {/* ── Workspace Nav ── */}
      <div style={{ padding: "0 12px" }}>
        <p className="section-header" style={{ padding: "8px 12px 8px" }}>Workspace</p>
        <nav className="flex flex-col" style={{ gap: 2 }}>
          {NAV_ITEMS.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => { setActiveTab(item.id); setMobileOpen(false); }}
                className="flex items-center gap-3 text-left relative"
                style={{
                  padding: "10px 12px",
                  borderRadius: "var(--radius-btn)",
                  fontSize: 13,
                  fontWeight: isActive ? 600 : 500,
                  color: isActive ? "var(--ink-primary)" : "var(--ink-secondary)",
                  background: isActive ? "var(--bg-elevated)" : "transparent",
                  transition: "all var(--dur-fast) var(--ease)",
                  fontFamily: "'Cabinet Grotesk', sans-serif",
                  border: "none",
                  cursor: "pointer",
                  width: "100%",
                }}
                onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = "var(--bg-elevated)"; }}
                onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = "transparent"; }}
              >
                {isActive && (
                  <div style={{
                    position: "absolute", left: 0, top: "50%", transform: "translateY(-50%)",
                    width: 3, height: 20, borderRadius: 2, background: "var(--amber)",
                  }} />
                )}
                <span style={{
                  fontSize: 16,
                  opacity: isActive ? 1 : 0.6,
                  color: isActive ? "var(--amber)" : "inherit",
                }}>
                  {item.icon}
                </span>
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* ── History ── */}
      <div style={{ padding: "16px 12px 0", flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
        <button
          onClick={() => setHistoryOpen(!historyOpen)}
          className="section-header flex items-center gap-2 w-full text-left"
          style={{ padding: "8px 12px", cursor: "pointer", border: "none", background: "none" }}
        >
          <span style={{
            fontSize: 8, transition: "transform 200ms",
            transform: historyOpen ? "rotate(90deg)" : "rotate(0deg)",
          }}>▸</span>
          Recent
        </button>
        {historyOpen && (
          <div style={{ flex: 1, overflowY: "auto", paddingBottom: 8 }}>
            {(!history || history.length === 0) ? (
              <p className="font-body" style={{ fontSize: 12, color: "var(--ink-tertiary)", padding: "8px 12px" }}>
                No summaries yet
              </p>
            ) : (
              history.map((entry, i) => {
                const time = formatTime(entry.timestamp);
                const preview = entry.inputText
                  ? (entry.inputText.length > 32 ? entry.inputText.slice(0, 32) + "…" : entry.inputText)
                  : "—";
                return (
                  <div
                    key={i}
                    className="flex items-start gap-2"
                    style={{
                      padding: "8px 12px", borderRadius: "var(--radius-btn)",
                      transition: "all var(--dur-fast) var(--ease)",
                      cursor: "pointer",
                      animation: `staggerItem 300ms var(--spring) forwards`,
                      animationDelay: `${i * 60}ms`,
                      opacity: 0,
                    }}
                    onClick={() => restoreFromHistory(entry)}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "var(--bg-elevated)";
                      e.currentTarget.style.paddingLeft = "16px";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "transparent";
                      e.currentTarget.style.paddingLeft = "12px";
                    }}
                  >
                    <span style={{ color: "var(--ink-tertiary)", fontSize: 10, marginTop: 4 }}>○</span>
                    <div className="min-w-0" style={{ flex: 1 }}>
                      <p className="truncate font-body" style={{ fontSize: 13, color: "var(--ink-secondary)", margin: 0 }}>{preview}</p>
                    </div>
                    <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-tertiary)", flexShrink: 0 }}>{time}</span>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>

      {/* ── Bottom ── */}
      <div style={{ borderTop: "1px solid var(--border-dim)", padding: "12px 16px" }}>
        {/* Theme toggle */}
        <div className="flex items-center justify-between mb-3">
          <span className="font-body" style={{ fontSize: 12, color: "var(--ink-secondary)" }}>Theme</span>
          <button
            onClick={toggleTheme}
            className="relative"
            style={{
              width: 52, height: 28, borderRadius: 14,
              background: dark ? "var(--bg-elevated)" : "var(--amber)",
              border: "1px solid var(--border-dim)", cursor: "pointer",
              transition: "background var(--dur-base) var(--ease)",
            }}
          >
            <div style={{
              width: 20, height: 20, borderRadius: 10,
              background: "var(--ink-primary)",
              position: "absolute", top: 3,
              left: dark ? 4 : 27,
              transition: "left var(--dur-base) var(--ease)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 10,
            }}>
              {dark ? "🌙" : "☀️"}
            </div>
          </button>
        </div>

        {/* QuillBot whisper */}
        <p className="font-mono" style={{
          fontSize: 10, color: "var(--ink-tertiary)", marginBottom: 12,
          opacity: 0.6,
        }}>
          ✦ Free forever · No ads · QuillBot Pro: $19.95/mo
        </p>

        {/* User area */}
        {user ? (
          <div className="relative">
            <button
              onClick={() => setAccountOpen(o => !o)}
              className="flex items-center gap-3 w-full text-left"
              style={{
                padding: "8px", borderRadius: "var(--radius-btn)",
                transition: "background var(--dur-fast) var(--ease)",
                border: "none", background: "none", cursor: "pointer",
                color: "var(--ink-primary)",
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = "var(--bg-elevated)"}
              onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
            >
              <div style={{
                width: 32, height: 32, borderRadius: 8,
                background: "var(--gradient-cta)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 13, fontWeight: 700, color: "#0B0906",
              }}>
                {initial}
              </div>
              <div className="min-w-0" style={{ flex: 1 }}>
                <p className="truncate font-body" style={{ fontSize: 12, fontWeight: 600, color: "var(--ink-primary)", margin: 0 }}>
                  {user.full_name || user.email?.split("@")[0]}
                </p>
                <p className="truncate font-mono" style={{ fontSize: 10, color: "var(--ink-tertiary)", margin: 0, marginTop: 2 }}>
                  {user.email}
                </p>
              </div>
            </button>

            {accountOpen && (
              <div style={{
                position: "absolute", bottom: "100%", left: 0, right: 0, marginBottom: 4,
                background: "var(--bg-overlay)", border: "1px solid var(--border-dim)",
                borderRadius: "var(--radius-card)", padding: 12, zIndex: 50,
                boxShadow: "var(--shadow-lift)",
              }}>
                <button
                  onClick={() => { setSettingsOpen(true); setAccountOpen(false); }}
                  className="btn-ghost w-full justify-center mb-2"
                >Manage Profile</button>
                <button
                  onClick={onLogout}
                  className="btn-ghost w-full justify-center"
                  style={{ color: "var(--rose)" }}
                >Log out</button>
              </div>
            )}
          </div>
        ) : (
          <button
            onClick={() => onOpenAuth("signup")}
            className="btn-ghost w-full justify-center"
            style={{ border: "1px solid var(--border-dim)" }}
          >
            Sign in
          </button>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="anim-sidebar" style={{
        display: "none",
        width: 248, flexShrink: 0, height: "100vh",
        position: "sticky", top: 0,
      }}>
        {sidebarContent}
      </aside>

      {/* Show sidebar on desktop via CSS */}
      <style>{`
        @media (min-width: 1024px) {
          aside.anim-sidebar { display: flex !important; }
        }
      `}</style>

      {/* Mobile hamburger */}
      <button
        onClick={() => setMobileOpen(true)}
        style={{
          display: "none",
          position: "fixed", top: 16, left: 16, zIndex: 50,
          width: 40, height: 40, borderRadius: "var(--radius-btn)",
          background: "var(--bg-surface)", border: "1px solid var(--border-dim)",
          alignItems: "center", justifyContent: "center",
          fontSize: 18, color: "var(--ink-primary)", cursor: "pointer",
        }}
      >
        ☰
      </button>
      <style>{`
        @media (max-width: 1023px) {
          button[style*="position: fixed"][style*="top: 16"] {
            display: flex !important;
          }
        }
      `}</style>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          onClick={() => setMobileOpen(false)}
          style={{
            position: "fixed", inset: 0, zIndex: 40,
            background: "rgba(11,9,6,0.7)",
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{ width: 280, height: "100%", animation: "slideIn 200ms ease forwards" }}
          >
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}