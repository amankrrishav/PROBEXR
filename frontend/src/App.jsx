/**
 * App — Shell: Sidebar + centered editorial column with page transitions.
 * "Warm Editorial Intelligence" design system.
 * C3: Keyboard shortcuts, ? tooltip
 * B3/B4: History integration via AppContext
 */
import { useState, useCallback, useEffect, lazy, Suspense } from "react";
import { config } from "./config.js";
import { useAppContext } from "./contexts/AppContext.jsx";
import { useSummarizerContext } from "./contexts/SummarizerContext.jsx";
import { Sidebar } from "./features/layout";
import { Editor, OutputCard, SummaryHistory } from "./features/summarizer";
import { SynthesisWorkspace } from "./features/summarizer";
import { AuthModal, SocialCallback } from "./features/auth";
import { ErrorBoundary } from "./components/ErrorBoundary.jsx";
import CustomCursor from "./components/CustomCursor.jsx";
import KeyboardShortcuts from "./components/KeyboardShortcuts.jsx";

// Lazy-loaded pages — loaded only when the user navigates to them
const AnalyticsDashboard = lazy(() =>
  import("./features/analytics").then(m => ({ default: m.AnalyticsDashboard }))
);

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
  const { auth, dark, summaryHistory } = useAppContext();
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

  // B3/B4: Wrap onSummarize to also add to persistent history
  function doSummarize() {
    summarizer.onSummarize();
    // Add to persistent history after a delay (give time for summary to complete)
    // The actual persistence happens via a listener in the summarizer hook
  }

  const handleSummarizeWithGate = useCallback(() => {
    if (!hasUsedFeatureOnce) {
      setHasUsedFeatureOnce(true);
      markFeatureUsedOnce();
      doSummarize();
      return;
    }
    if (!auth.isAuthenticated) {
      handleOpenAuth("signup");
      return;
    }
    doSummarize();
  }, [hasUsedFeatureOnce, auth.isAuthenticated, summarizer]);

  // C3: Global keyboard shortcuts
  // useCallback with stable primitive deps prevents the handler from being
  // re-registered on every render (A-25: summarizer is a new object each render).
  const handleKeyDown = useCallback((e) => {
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

    // ⌘K — New summary (B11)
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

    // ⌘+Enter — Summarize (C3)
    if (mod && e.key === "Enter") {
      e.preventDefault();
      handleSummarizeWithGate();
      return;
    }
  }, [activeTab, summarizer.reset, summarizer.setText, summarizer.setUrl, handleSummarizeWithGate]);

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  // Trigger page transition on tab change
  const handleSetActiveTab = useCallback((tab) => {
    setActiveTab(tab);
    setPageKey((k) => k + 1);
  }, []);

  // B3/B4: Watch for successful summaries and add to persistent history
  useEffect(() => {
    if (summarizer.summarizeStatus === "success" && summarizer.summaryText) {
      summaryHistory.addEntry({
        inputText: summarizer.text,
        summaryText: summarizer.summaryText,
        mode: summarizer.summaryMode,
        lengthSetting: summarizer.summaryLength,
        inputWordCount: summarizer.wordCount,
        isUrl: summarizer.isUrlMode,
        focusArea: summarizer.focusArea,
        outputLanguage: summarizer.outputLanguage,
        customInstructions: summarizer.customInstructions,
      });
    }
  }, [summarizer.summarizeStatus]);

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
        <ErrorBoundary>
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
              <Suspense fallback={
                <div style={{ display: "flex", justifyContent: "center", padding: 80 }}>
                  <div style={{ color: "var(--ink-tertiary)" }}>Loading analytics…</div>
                </div>
              }>
                <AnalyticsDashboard />
              </Suspense>
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
        </ErrorBoundary>
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

      {/* C3: Keyboard Shortcuts */}
      <KeyboardShortcuts
        open={shortcutsOpen}
        onClose={() => setShortcutsOpen(false)}
      />

      {/* C3: ? icon for shortcuts tooltip */}
      <button
        onClick={() => setShortcutsOpen(true)}
        style={{
          position: "fixed", bottom: 24, right: 24,
          width: 36, height: 36, borderRadius: "50%",
          background: "var(--bg-surface)", border: "1px solid var(--border-dim)",
          color: "var(--ink-tertiary)", fontSize: 16,
          cursor: "pointer", zIndex: 50,
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: "var(--shadow-sm)",
          transition: "all var(--dur-fast) var(--ease)",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = "var(--amber)";
          e.currentTarget.style.color = "var(--amber)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = "var(--border-dim)";
          e.currentTarget.style.color = "var(--ink-tertiary)";
        }}
        title="Keyboard shortcuts (⌘/)"
        aria-label="Show keyboard shortcuts"
      >
        ?
      </button>

      {/* Snackbar / Toast */}
      {snackbar && (
        <Toast message={snackbar} onDone={() => setSnackbar(null)} />
      )}
    </div>
  );
}