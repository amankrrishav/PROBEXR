/**
 * App — Shell: Sidebar + centered editorial column with page transitions.
 * "Warm Editorial Intelligence" design system.
 */
import { useState, useCallback, useEffect } from "react";
import { config } from "./config.js";
import { useAppContext } from "./contexts/AppContext.jsx";
import { useSummarizerContext } from "./contexts/SummarizerContext.jsx";
import { Sidebar } from "./features/layout";
import { Editor, OutputCard, SummaryHistory } from "./features/summarizer";
import { SynthesisWorkspace } from "./features/summarizer";
import { AuthModal, SocialCallback } from "./features/auth";
import { AnalyticsDashboard } from "./features/analytics";
import CustomCursor from "./components/CustomCursor.jsx";
import KeyboardShortcuts from "./components/KeyboardShortcuts.jsx";

const USAGE_KEY = "probexr.hasUsedFeatureOnce";

function isBrowser() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

/* ── Toast Component ── */
function Toast({ message, onDone }) {
  const [exiting, setExiting] = useState(false);
  useEffect(() => {
    const t1 = setTimeout(() => setExiting(true), 2000);
    const t2 = setTimeout(() => onDone(), 2300);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [onDone]);
  return <div className={`toast${exiting ? " exiting" : ""}`}>{message}</div>;
}

export default function App() {
  const { auth, dark } = useAppContext();
  const summarizer = useSummarizerContext();

  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState("signup");
  const [pageKey, setPageKey] = useState(0);

  // Simple routing for auth callbacks
  const pathname = window.location.pathname;
  const isSocialCallback = pathname.startsWith("/auth/callback/");
  const isMagicVerify = pathname === "/auth/verify";
  const authProvider = isSocialCallback ? pathname.split("/").pop() : isMagicVerify ? "verify" : null;
  const isCallback = isSocialCallback || isMagicVerify;

  const [hasUsedFeatureOnce, setHasUsedFeatureOnce] = useState(() => {
    if (!isBrowser()) return false;
    try { return window.localStorage.getItem(USAGE_KEY) === "true"; } catch { return false; }
  });
  const [snackbar, setSnackbar] = useState(null);
  const [activeTab, setActiveTab] = useState("summarize");
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [focusMode, setFocusMode] = useState(false);

  // Apply dark/light class to root element
  useEffect(() => {
    document.documentElement.classList.toggle("light", !dark);
  }, [dark]);

  // Global keyboard shortcuts
  useEffect(() => {
    function handleKeyDown(e) {
      const mod = e.metaKey || e.ctrlKey;

      // ⌘/ — Keyboard shortcuts
      if (mod && e.key === "/") {
        e.preventDefault();
        setShortcutsOpen(o => !o);
        return;
      }

      // ⌘F — Focus mode
      if (mod && e.key === "f" && activeTab === "summarize") {
        e.preventDefault();
        setFocusMode(f => !f);
        return;
      }

      // ⌘K — New summary
      if (mod && e.key === "k") {
        e.preventDefault();
        summarizer.reset();
        setActiveTab("summarize");
        return;
      }

      // ⌘+Shift+C — Clear input
      if (mod && e.shiftKey && e.key === "C") {
        e.preventDefault();
        summarizer.setText("");
        summarizer.setUrl("");
        return;
      }

      // Escape — exit modals/focus mode
      if (e.key === "Escape") {
        setShortcutsOpen(false);
        setFocusMode(false);
        return;
      }

      // ⌘+Enter — Summarize
      if (mod && e.key === "Enter") {
        e.preventDefault();
        handleSummarizeWithGate();
        return;
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [activeTab, summarizer]);

  // Trigger page transition on tab change
  const handleSetActiveTab = useCallback((tab) => {
    setActiveTab(tab);
    setPageKey((k) => k + 1);
  }, []);

  function markFeatureUsedOnce() {
    if (!isBrowser()) return;
    try { window.localStorage.setItem(USAGE_KEY, "true"); } catch { /* ignore */ }
  }

  function handleOpenAuth(mode = "signup") {
    setAuthModalMode(mode);
    setAuthModalOpen(true);
  }

  function showSnackbar(message) {
    setSnackbar(message);
    window.setTimeout(() => setSnackbar(null), 2500);
  }

  function handleLogout() {
    auth.logout();
    showSnackbar("Logged out.");
  }

  const handleSummarizeWithGate = useCallback(() => {
    if (!hasUsedFeatureOnce) {
      setHasUsedFeatureOnce(true);
      markFeatureUsedOnce();
      summarizer.onSummarize();
      return;
    }
    if (!auth.isAuthenticated) {
      handleOpenAuth("signup");
      return;
    }
    summarizer.onSummarize();
  }, [hasUsedFeatureOnce, auth.isAuthenticated, summarizer]);

  if (isCallback) {
    return (
      <SocialCallback
        provider={authProvider}
        onResult={(success) => {
          window.setTimeout(() => { window.location.href = "/"; }, success ? 500 : 2000);
        }}
      />
    );
  }

  return (
    <div className={focusMode ? "focus-mode-active" : ""} style={{ display: "flex", minHeight: "100vh", background: "var(--bg-base)", color: "var(--ink-primary)" }}>
      {/* Living background orbs */}
      <div className="bg-orb-a anim-orbs" />
      <div className="bg-orb-b anim-orbs" />

      {/* Custom cursor (desktop only) */}
      <CustomCursor />

      {/* Sidebar */}
      <div className="focus-fade">
        <Sidebar
          appName={config.appName}
          onOpenAuth={handleOpenAuth}
          onLogout={handleLogout}
          activeTab={activeTab}
          setActiveTab={handleSetActiveTab}
        />
      </div>

      {/* Main content */}
      <main style={{ flex: 1, minWidth: 0, overflowY: "auto", minHeight: "100vh", position: "relative", zIndex: 1 }}>
        <div key={pageKey} className="page-enter" style={{ padding: "48px 40px" }}>

          {activeTab === "summarize" ? (
            <div style={{ maxWidth: 720, margin: "0 auto" }}>
              {/* Input Card */}
              <Editor
                onSummarize={handleSummarizeWithGate}
                handleKeyDown={(e) => {
                  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
                    e.preventDefault();
                    handleSummarizeWithGate();
                  }
                }}
                focusMode={focusMode}
              />

              {/* Output Card (appears below input, animates in) */}
              {summarizer.hasSummary && (
                <div className="anim-output-reveal" style={{ marginTop: 32 }}>
                  <OutputCard />
                </div>
              )}

              {/* Summary History */}
              {summarizer.hasSummary && (
                <div style={{ marginTop: 16 }}>
                  <SummaryHistory />
                </div>
              )}
            </div>
          ) : activeTab === "analytics" ? (
            <div style={{ maxWidth: 1200, margin: "0 auto" }}>
              <div style={{ marginBottom: 32 }}>
                <h1 className="font-display" style={{ fontSize: 32, color: "var(--ink-primary)" }}>
                  Analytics
                </h1>
                <p className="font-body" style={{ fontSize: 14, color: "var(--ink-secondary)", marginTop: 4 }}>
                  Your summarization insights and history
                </p>
              </div>
              <AnalyticsDashboard />
            </div>
          ) : (
            <div style={{ maxWidth: 960, margin: "0 auto" }}>
              <div style={{ marginBottom: 32 }}>
                <h1 className="font-display" style={{ fontSize: 32, color: "var(--ink-primary)" }}>
                  Multi-Doc Synthesis
                </h1>
                <p className="font-body" style={{ fontSize: 14, color: "var(--ink-secondary)", marginTop: 4 }}>
                  Compare and merge multiple documents
                </p>
              </div>
              <SynthesisWorkspace />
            </div>
          )}
        </div>
      </main>

      {/* Auth Modal */}
      <AuthModal
        open={authModalOpen}
        mode={authModalMode}
        onModeChange={setAuthModalMode}
        onClose={() => setAuthModalOpen(false)}
        onLogin={auth.login}
        onRegister={auth.register}
        submitting={auth.submitting}
        error={auth.error}
        onSuccess={showSnackbar}
      />

      {/* Keyboard Shortcuts */}
      <KeyboardShortcuts
        open={shortcutsOpen}
        onClose={() => setShortcutsOpen(false)}
      />

      {/* Snackbar / Toast */}
      {snackbar && (
        <Toast message={snackbar} onDone={() => setSnackbar(null)} />
      )}
    </div>
  );
}
