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
  const { reset, history } = useSummarizerContext();
  const [accountOpen, setAccountOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);

  const initial = user?.full_name
    ? user.full_name.charAt(0).toUpperCase()
    : user?.email
      ? user.email.charAt(0).toUpperCase()
      : null;

  const sidebarContent = (
    <div className="flex flex-col h-full" style={{ background: "var(--bg-surface)", borderRight: "1px solid var(--border)" }}>
      <AccountSettings open={settingsOpen} onClose={() => setSettingsOpen(false)} />

      {/* ── Brand ── */}
      <div style={{ padding: "24px 24px 16px" }}>
        <h1 className="font-display gradient-text" style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-0.02em" }}>
          {appName ?? "PROBEXR"}
        </h1>
        {backendMode && (
          <div className="flex items-center gap-2 mt-2">
            <div className="pulse-dot" />
            <span className="font-mono" style={{ fontSize: 11, color: "var(--text-tertiary)" }}>
              Backend: {backendMode}
            </span>
          </div>
        )}
      </div>

      {/* ── New Summary CTA ── */}
      <div style={{ padding: "0 16px 16px" }}>
        <button
          onClick={() => { setActiveTab("summarize"); reset(); setMobileOpen(false); }}
          className="btn-primary w-full"
          style={{ height: 44, fontSize: 14, background: "var(--gradient-hero)" }}
        >
          <span style={{ display: "inline-block", transition: "transform 200ms" }}>✦</span>
          New Summary
        </button>
      </div>

      {/* ── Workspace Nav ── */}
      <div style={{ padding: "0 12px" }}>
        <p className="section-header" style={{ padding: "8px 12px 8px" }}>Workspace</p>
        <nav className="flex flex-col gap-1">
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
                  color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                  background: isActive ? "var(--bg-elevated)" : "transparent",
                  transition: "all var(--duration-fast) var(--ease)",
                  fontFamily: "'Plus Jakarta Sans', sans-serif",
                }}
                onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = "var(--bg-elevated)"; }}
                onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = "transparent"; }}
              >
                {isActive && (
                  <div style={{
                    position: "absolute", left: 0, top: "50%", transform: "translateY(-50%)",
                    width: 3, height: 20, borderRadius: 2, background: "var(--accent)",
                  }} />
                )}
                <span style={{ fontSize: 16, opacity: isActive ? 1 : 0.6, color: isActive ? "var(--accent)" : "inherit" }}>
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
          History
        </button>
        {historyOpen && (
          <div className="flex-1 overflow-y-auto" style={{ paddingBottom: 8 }}>
            {(!history || history.length === 0) ? (
              <p className="font-body" style={{ fontSize: 12, color: "var(--text-tertiary)", padding: "8px 12px" }}>
                No summaries yet
              </p>
            ) : (
              history.map((entry, i) => {
                const time = entry.timestamp
                  ? new Date(entry.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                  : "";
                const preview = entry.inputText
                  ? (entry.inputText.length > 35 ? entry.inputText.slice(0, 35) + "…" : entry.inputText)
                  : "—";
                return (
                  <div
                    key={i}
                    className="flex items-start gap-2 cursor-pointer"
                    style={{
                      padding: "8px 12px", borderRadius: "var(--radius-btn)",
                      transition: "background var(--duration-fast) var(--ease)",
                    }}
                    onClick={() => { /* TODO: restore from history */ }}
                    onMouseEnter={(e) => e.currentTarget.style.background = "var(--bg-elevated)"}
                    onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                  >
                    <span style={{ color: "var(--text-tertiary)", fontSize: 12, marginTop: 2 }}>○</span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-body" style={{ fontSize: 12, color: "var(--text-secondary)" }}>{preview}</p>
                      <p className="font-mono" style={{ fontSize: 10, color: "var(--text-tertiary)", marginTop: 2 }}>{time}</p>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>

      {/* ── Bottom ── */}
      <div style={{ borderTop: "1px solid var(--border)", padding: "12px 16px" }}>
        {/* Theme toggle */}
        <div className="flex items-center justify-between mb-3">
          <span className="font-body" style={{ fontSize: 12, color: "var(--text-secondary)" }}>Theme</span>
          <button
            onClick={toggleTheme}
            className="relative"
            style={{
              width: 52, height: 28, borderRadius: 14,
              background: dark ? "var(--bg-elevated)" : "var(--accent)",
              border: "1px solid var(--border)", cursor: "pointer",
              transition: "background var(--duration-base) var(--ease)",
            }}
          >
            <div style={{
              width: 20, height: 20, borderRadius: 10,
              background: "var(--text-primary)",
              position: "absolute", top: 3,
              left: dark ? 4 : 27,
              transition: "left var(--duration-base) var(--ease)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 10,
            }}>
              {dark ? "🌙" : "☀️"}
            </div>
          </button>
        </div>

        {/* User area */}
        {user ? (
          <div className="relative">
            <button
              onClick={() => setAccountOpen(o => !o)}
              className="flex items-center gap-3 w-full text-left"
              style={{
                padding: "8px", borderRadius: "var(--radius-btn)",
                transition: "background var(--duration-fast) var(--ease)",
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = "var(--bg-elevated)"}
              onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
            >
              <div style={{
                width: 32, height: 32, borderRadius: 8,
                background: "var(--gradient-hero)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 13, fontWeight: 700, color: "white",
              }}>
                {initial}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate font-body" style={{ fontSize: 12, fontWeight: 600, color: "var(--text-primary)" }}>
                  {user.full_name || user.email?.split("@")[0]}
                </p>
                <p className="truncate font-mono" style={{ fontSize: 10, color: "var(--text-tertiary)" }}>
                  {user.email}
                </p>
              </div>
            </button>

            {accountOpen && (
              <div style={{
                position: "absolute", bottom: "100%", left: 0, right: 0, marginBottom: 4,
                background: "var(--bg-overlay)", border: "1px solid var(--border)",
                borderRadius: "var(--radius-card)", padding: 12, zIndex: 50,
                boxShadow: "var(--shadow-lg)",
              }}>
                <button
                  onClick={() => { setSettingsOpen(true); setAccountOpen(false); }}
                  className="btn-ghost w-full justify-center mb-2"
                >Manage Profile</button>
                <button
                  onClick={onLogout}
                  className="btn-ghost w-full justify-center"
                  style={{ color: "var(--accent-warn)" }}
                >Log out</button>
              </div>
            )}
          </div>
        ) : (
          <button
            onClick={() => onOpenAuth("signup")}
            className="btn-ghost w-full justify-center"
            style={{ border: "1px solid var(--border)" }}
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
      <aside className="hidden lg:flex w-[260px] shrink-0 h-screen sticky top-0">
        {sidebarContent}
      </aside>

      {/* Mobile hamburger */}
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-50"
        style={{
          width: 40, height: 40, borderRadius: "var(--radius-btn)",
          background: "var(--bg-surface)", border: "1px solid var(--border)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 18, color: "var(--text-primary)", cursor: "pointer",
        }}
      >
        ☰
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40"
          onClick={() => setMobileOpen(false)}
          style={{ background: "rgba(0,0,0,0.6)" }}
        >
          <div
            className="w-[280px] h-full"
            onClick={(e) => e.stopPropagation()}
            style={{ animation: "slideIn 200ms ease forwards" }}
          >
            {sidebarContent}
          </div>
        </div>
      )}

      <style>{`
        @keyframes slideIn {
          from { transform: translateX(-100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </>
  );
}