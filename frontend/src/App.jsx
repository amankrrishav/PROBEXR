/**
 * App — thin shell: composes config, hooks, and features (like backend main.py).
 * Add new features: new hook + feature folder, then wire here.
 */
import { useEffect, useState } from "react";
import { config } from "./config.js";
import { useSummarizer } from "./hooks/useSummarizer.js";
import { useTheme } from "./hooks/useTheme.js";
import { useBackendHealth } from "./hooks/useBackendHealth.js";
import { useAuth } from "./hooks/useAuth.js";
import { Sidebar } from "./features/layout";
import { Editor, OutputCard } from "./features/summarizer";
import { AuthModal } from "./features/auth";

const USAGE_KEY = "readpulse.hasUsedFeatureOnce";

function isBrowser() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

export default function App() {
  const { dark, toggleTheme } = useTheme();
  const summarizer = useSummarizer();
  const { backendMode } = useBackendHealth();
   const auth = useAuth();

  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState("signup");
  const [hasUsedFeatureOnce, setHasUsedFeatureOnce] = useState(false);
  const [snackbar, setSnackbar] = useState(null);

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

  function handleSummarizeWithGate() {
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
  }

  return (
    <div className="h-screen flex bg-[#F8F7F4] text-[#1A1A2E] dark:bg-[#0a0a0a] dark:text-white transition-colors duration-300">
      <Sidebar
        dark={dark}
        toggleTheme={toggleTheme}
        resetWorkspace={summarizer.reset}
        appName={config.appName}
        backendMode={backendMode}
        user={auth.user}
        onOpenAuth={handleOpenAuth}
        onLogout={handleLogout}
      />
      <main className="flex-1 overflow-y-auto">
        <div
          className={`px-12 py-16 transition-all duration-500 ${
            summarizer.hasSummary
              ? "grid grid-cols-2 gap-12"
              : "max-w-3xl mx-auto"
          }`}
        >
          <Editor
            text={summarizer.text}
            setText={summarizer.setText}
            loading={summarizer.loading}
            loadingMessage={summarizer.loadingMessage}
            error={summarizer.error}
            wordCount={summarizer.wordCount}
            charCount={summarizer.charCount}
            hasSummary={summarizer.hasSummary}
            onSummarize={handleSummarizeWithGate}
            handleKeyDown={summarizer.handleKeyDown}
          />
          {summarizer.hasSummary && (
            <OutputCard summaryText={summarizer.summaryText} />
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
