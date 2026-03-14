/**
 * Summary history — persists to localStorage under probexr_history.
 * Max 20 entries. Provides analytics computed from history.
 */
import { useState, useCallback, useMemo } from "react";

const STORAGE_KEY = "probexr_history";
const MAX_ENTRIES = 20;

function loadHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveHistory(entries) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  } catch {
    // quota exceeded — silently fail
  }
}

let _nextId = Date.now();

export function useSummaryHistory() {
  const [history, setHistory] = useState(loadHistory);

  const addEntry = useCallback((entry) => {
    setHistory((prev) => {
      const newEntry = {
        id: _nextId++,
        title: (entry.inputText || "").slice(0, 40) || "Untitled",
        mode: entry.mode || "paragraph",
        lengthSetting: entry.lengthSetting || "standard",
        inputWordCount: entry.inputWordCount || 0,
        timestamp: entry.timestamp || new Date().toISOString(),
        inputText: entry.inputText || "",
        summaryText: entry.summaryText || "",
        isUrl: entry.isUrl || false,
        focusArea: entry.focusArea || "",
        outputLanguage: entry.outputLanguage || "English",
        customInstructions: entry.customInstructions || "",
      };
      const next = [newEntry, ...prev].slice(0, MAX_ENTRIES);
      saveHistory(next);
      return next;
    });
  }, []);

  const removeEntry = useCallback((id) => {
    setHistory((prev) => {
      const next = prev.filter((e) => e.id !== id);
      saveHistory(next);
      return next;
    });
  }, []);

  const clearAll = useCallback(() => {
    setHistory([]);
    saveHistory([]);
  }, []);

  // Computed analytics
  const analytics = useMemo(() => {
    if (history.length === 0) {
      return {
        totalSummaries: 0,
        mostUsedMode: null,
        modeBreakdown: [],
        avgWordCount: 0,
        lengthBreakdown: { brief: 0, standard: 0, detailed: 0 },
      };
    }

    // Mode breakdown
    const modeCounts = {};
    const lengthCounts = { brief: 0, standard: 0, detailed: 0 };
    let totalWords = 0;

    for (const entry of history) {
      modeCounts[entry.mode] = (modeCounts[entry.mode] || 0) + 1;
      if (entry.lengthSetting in lengthCounts) {
        lengthCounts[entry.lengthSetting]++;
      }
      totalWords += entry.inputWordCount || 0;
    }

    const modeBreakdown = Object.entries(modeCounts)
      .map(([mode, count]) => ({ mode, count, pct: Math.round((count / history.length) * 100) }))
      .sort((a, b) => b.count - a.count);

    const total = history.length;
    const lengthBreakdown = {
      brief: Math.round((lengthCounts.brief / total) * 100),
      standard: Math.round((lengthCounts.standard / total) * 100),
      detailed: Math.round((lengthCounts.detailed / total) * 100),
    };

    return {
      totalSummaries: total,
      mostUsedMode: modeBreakdown[0]?.mode || null,
      modeBreakdown,
      avgWordCount: Math.round(totalWords / total),
      lengthBreakdown,
    };
  }, [history]);

  return {
    history,
    addEntry,
    removeEntry,
    clearAll,
    analytics,
  };
}
