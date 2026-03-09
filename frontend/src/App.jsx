/**
 * App — Shell: Sidebar + routed content area with page transitions.
 * Uses the design system CSS variables for all theming.
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

const USAGE_KEY = "probexr.hasUsedFeatureOnce";

function isBrowser() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

export default function App() {
  const { auth, dark } = useAppContext();
  const summarizer = useSummarizerContext();

  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState("signup");
  const [pageKey, setPageKey] = useState(0); // for page transitions

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

  // Apply dark/light class to root element
  useEffect(() => {
    document.documentElement.classList.toggle("light", !dark);
  }, [dark]);

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

  // Page titles
  const PAGE_META = {
    summarize:  { title: "Single Document", subtitle: "Summarize any text with AI precision" },
    synthesize: { title: "Multi-Doc Synthesis", subtitle: "Compare and merge multiple documents" },
    analytics:  { title: "Analytics", subtitle: "Your summarization insights and history" },
  };
  const meta = PAGE_META[activeTab] || PAGE_META.summarize;

  return (
    <div className="flex min-h-screen" style={{ background: "var(--bg-base)", color: "var(--text-primary)" }}>
      <Sidebar
        appName={config.appName}
        onOpenAuth={handleOpenAuth}
        onLogout={handleLogout}
        activeTab={activeTab}
        setActiveTab={handleSetActiveTab}
      />

      <main className="flex-1 min-w-0 overflow-y-auto" style={{ minHeight: "100vh" }}>
        {/* Page content with transition */}
        <div key={pageKey} className="page-enter" style={{ padding: activeTab === "summarize" && summarizer.hasSummary ? "32px 40px" : "48px 40px" }}>

          {activeTab === "summarize" ? (
            <>
              {/* Two-panel layout when summary exists */}
              {summarizer.hasSummary ? (
                <div className="flex gap-8" style={{ minHeight: "calc(100vh - 64px)" }}>
                  {/* Left — Input (45%) */}
                  <div className="w-[45%] shrink-0" style={{ maxHeight: "calc(100vh - 64px)", overflowY: "auto" }}>
                    <Editor
                      onSummarize={handleSummarizeWithGate}
                      handleKeyDown={(e) => {
                        if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
                          e.preventDefault();
                          handleSummarizeWithGate();
                        }
                      }}
                    />
                  </div>
                  {/* Right — Output (55%) */}
                  <div className="flex-1 min-w-0" style={{ maxHeight: "calc(100vh - 64px)", overflowY: "auto" }}>
                    <OutputCard />
                    <div style={{ marginTop: 16 }}>
                      <SummaryHistory />
                    </div>
                  </div>
                </div>
              ) : (
                /* Single column before summary */
                <div style={{ maxWidth: 720, margin: "0 auto" }}>
                  <Editor
                    onSummarize={handleSummarizeWithGate}
                    handleKeyDown={(e) => {
                      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
                        e.preventDefault();
                        handleSummarizeWithGate();
                      }
                    }}
                  />
                </div>
              )}
            </>
          ) : activeTab === "analytics" ? (
            <div style={{ maxWidth: 1200, margin: "0 auto" }}>
              <div style={{ marginBottom: 32 }}>
                <h1 className="font-display" style={{ fontSize: 28, fontWeight: 700, color: "var(--text-primary)" }}>{meta.title}</h1>
                <p className="font-body" style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 4 }}>{meta.subtitle}</p>
              </div>
              <AnalyticsDashboard />
            </div>
          ) : (
            <div style={{ maxWidth: 1200, margin: "0 auto" }}>
              <div style={{ marginBottom: 32 }}>
                <h1 className="font-display" style={{ fontSize: 28, fontWeight: 700, color: "var(--text-primary)" }}>{meta.title}</h1>
                <p className="font-body" style={{ fontSize: 14, color: "var(--text-secondary)", marginTop: 4 }}>{meta.subtitle}</p>
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

      {/* Snackbar */}
      {snackbar && (
        <div className="pointer-events-none fixed inset-x-0 bottom-5 z-40 flex justify-center">
          <div className="pointer-events-auto animate-in" style={{
            padding: "10px 20px", borderRadius: "var(--radius-btn)",
            background: "var(--bg-overlay)", border: "1px solid var(--border)",
            fontSize: 13, fontWeight: 500, color: "var(--text-primary)",
            boxShadow: "var(--shadow-lg)",
          }}>
            {snackbar}
          </div>
        </div>
      )}
    </div>
  );
}
