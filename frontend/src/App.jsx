/**
 * App — thin shell: composes config, hooks, and features (like backend main.py).
 * Add new features: new hook + feature folder, then wire here.
 */
import { useState, useCallback } from "react";
import { config } from "./config.js";
import { useAppContext } from "./contexts/AppContext.jsx";
import { useSummarizerContext } from "./contexts/SummarizerContext.jsx";
import { Sidebar } from "./features/layout";
import { Editor, OutputCard, SynthesisWorkspace } from "./features/summarizer";
import { AuthModal } from "./features/auth";
import { AnalyticsDashboard } from "./features/analytics";

const USAGE_KEY = "readpulse.hasUsedFeatureOnce";

function isBrowser() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

export default function App() {
  const { auth } = useAppContext();
  const summarizer = useSummarizerContext();

  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState("signup");
  const [hasUsedFeatureOnce, setHasUsedFeatureOnce] = useState(() => {
    if (!isBrowser()) return false;
    try {
      return window.localStorage.getItem(USAGE_KEY) === "true";
    } catch {
      return false;
    }
  });
  const [snackbar, setSnackbar] = useState(null);
  const [activeTab, setActiveTab] = useState("summarize");

  function markFeatureUsedOnce() {
    if (!isBrowser()) return;
    try {
      window.localStorage.setItem(USAGE_KEY, "true");
    } catch {
      // ignore
    }
  }

  function handleOpenAuth(mode = "signup") {
    setAuthModalMode(mode);
    setAuthModalOpen(true);
  }

  function handleCloseAuth() {
    setAuthModalOpen(false);
  }

  function showSnackbar(message) {
    setSnackbar(message);
    window.setTimeout(() => {
      setSnackbar(null);
    }, 2500);
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

  return (
    <div className="h-screen flex bg-[#F8F7F4] text-[#1A1A2E] dark:bg-[#0a0a0a] dark:text-white transition-colors duration-300">
      <Sidebar
        appName={config.appName}
        onOpenAuth={handleOpenAuth}
        onLogout={handleLogout}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />
      <main className="flex-1 overflow-y-auto">
        <div
          className={`transition-all duration-500 ${activeTab === 'summarize' && summarizer.hasSummary
            ? "grid grid-cols-2 gap-10 px-14 py-14"
            : activeTab === "analytics"
              ? "max-w-5xl mx-auto px-12 py-12"
              : "max-w-2xl mx-auto px-8 py-16"
            }`}
        >
          {activeTab === "summarize" ? (
            <>
              <Editor
                onSummarize={handleSummarizeWithGate}
                handleKeyDown={(e) => {
                  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
                    e.preventDefault();
                    handleSummarizeWithGate();
                  }
                }}
              />
              {summarizer.hasSummary && (
                <OutputCard />
              )}
            </>
          ) : activeTab === "analytics" ? (
            <AnalyticsDashboard />
          ) : (
            <SynthesisWorkspace />
          )}
        </div>
      </main>

      <AuthModal
        open={authModalOpen}
        mode={authModalMode}
        onModeChange={setAuthModalMode}
        onClose={handleCloseAuth}
        onLogin={auth.login}
        onRegister={auth.register}
        submitting={auth.submitting}
        error={auth.error}
        onSuccess={showSnackbar}
      />

      {snackbar && (
        <div className="pointer-events-none fixed inset-x-0 bottom-5 z-40 flex justify-center">
          <div className="pointer-events-auto rounded-full bg-black px-4 py-2 text-xs text-white shadow-lg dark:bg-white dark:text-black">
            {snackbar}
          </div>
        </div>
      )}
    </div>
  );
}
