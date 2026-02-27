/**
 * App — thin shell: composes config, hooks, and features (like backend main.py).
 * Add new features: new hook + feature folder, then wire here.
 */
import { useEffect, useState, useCallback } from "react";
import { config } from "./config.js";
import { useAppContext } from "./contexts/AppContext.jsx";
import { useSummarizerContext } from "./contexts/SummarizerContext.jsx";
import { Sidebar } from "./features/layout";
import { Editor, OutputCard, SynthesisWorkspace } from "./features/summarizer";
import { AuthModal } from "./features/auth";
import { ProModal } from "./features/subscription";

const USAGE_KEY = "readpulse.hasUsedFeatureOnce";

function isBrowser() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

export default function App() {
  const { dark, auth, subscription } = useAppContext();
  const summarizer = useSummarizerContext();

  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState("signup");
  const [hasUsedFeatureOnce, setHasUsedFeatureOnce] = useState(false);
  const [snackbar, setSnackbar] = useState(null);
  const [proModalOpen, setProModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("summarize");

  useEffect(() => {
    if (!isBrowser()) return;
    try {
      const flag = window.localStorage.getItem(USAGE_KEY);
      setHasUsedFeatureOnce(flag === "true");
    } catch {
      // ignore
    }
  }, []);

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

  function handleOpenProModal() {
    setProModalOpen(true);
  }

  function handleCloseProModal() {
    setProModalOpen(false);
  }

  async function handleUpgradeProDemo() {
    try {
      await auth.upgradeToDemoPro();
      showSnackbar("Pro Mode activated (demo).");
      handleCloseProModal();
    } catch {
      // error is shown inside the modal
    }
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
  }, [hasUsedFeatureOnce, auth.isAuthenticated, summarizer.onSummarize]);

  return (
    <div className="h-screen flex bg-[#F8F7F4] text-[#1A1A2E] dark:bg-[#0a0a0a] dark:text-white transition-colors duration-300">
      <Sidebar
        appName={config.appName}
        onOpenAuth={handleOpenAuth}
        onLogout={handleLogout}
        onOpenPro={handleOpenProModal}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />
      <main className="flex-1 overflow-y-auto">
        {subscription.overLimit && (
          <div className="mx-12 mt-6 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-xs text-amber-900 dark:border-amber-500/40 dark:bg-amber-900/20 dark:text-amber-100">
            <span className="font-medium">Free limit reached.</span>{" "}
            Summaries now use Lite mode (simpler extractive summaries).{" "}
            <button
              type="button"
              onClick={handleOpenProModal}
              className="underline underline-offset-2"
            >
              Learn about Pro Mode
            </button>{" "}
            to keep high-quality LLM summaries all day.
          </div>
        )}
        <div
          className={`px-12 py-16 transition-all duration-500 ${activeTab === 'summarize' && summarizer.hasSummary
            ? "grid grid-cols-2 gap-12"
            : "max-w-3xl mx-auto"
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

      <ProModal
        open={proModalOpen}
        onClose={handleCloseProModal}
        onUpgrade={handleUpgradeProDemo}
        submitting={auth.submitting}
        error={auth.error}
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
