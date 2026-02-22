/**
 * App — thin shell: composes config, hooks, and features (like backend main.py).
 * Add new features: new hook + feature folder, then wire here.
 */
import { useSummarizer } from "./hooks/useSummarizer.js";
import { useTheme } from "./hooks/useTheme.js";
import { Sidebar } from "./features/layout";
import { Editor, OutputCard } from "./features/summarizer";

export default function App() {
  const { dark, toggleTheme } = useTheme();
  const summarizer = useSummarizer();

  return (
    <div className="h-screen flex bg-[#F8F7F4] text-[#1A1A2E] dark:bg-[#0a0a0a] dark:text-white transition-colors duration-300">
      <Sidebar
        dark={dark}
        toggleTheme={toggleTheme}
        resetWorkspace={summarizer.reset}
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
            onSummarize={summarizer.onSummarize}
            handleKeyDown={summarizer.handleKeyDown}
          />
          {summarizer.hasSummary && (
            <OutputCard summaryText={summarizer.summaryText} />
          )}
        </div>
      </main>
    </div>
  );
}
