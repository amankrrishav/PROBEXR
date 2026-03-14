/**
 * Theme state and persistence — uses probexr_theme key.
 * Falls back to prefers-color-scheme if no stored preference.
 */
import { useEffect, useState } from "react";

const STORAGE_KEY = "probexr_theme";

function getInitialDark() {
  if (typeof window === "undefined") return false;
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "dark") return true;
  if (stored === "light") return false;
  // Fall back to system preference
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
}

export function useTheme() {
  const [dark, setDark] = useState(getInitialDark);

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add("dark");
      document.documentElement.classList.remove("light");
    } else {
      document.documentElement.classList.remove("dark");
      document.documentElement.classList.add("light");
    }
  }, [dark]);

  function toggleTheme() {
    const next = !dark;
    if (next) {
      document.documentElement.classList.add("dark");
      document.documentElement.classList.remove("light");
      localStorage.setItem(STORAGE_KEY, "dark");
    } else {
      document.documentElement.classList.remove("dark");
      document.documentElement.classList.add("light");
      localStorage.setItem(STORAGE_KEY, "light");
    }
    setDark(next);
  }

  return { dark, toggleTheme };
}
