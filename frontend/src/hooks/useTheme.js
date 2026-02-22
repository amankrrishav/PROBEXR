/**
 * Theme state and persistence — keeps App thin. Add other app-wide hooks here.
 */
import { useEffect, useState } from "react";

const STORAGE_KEY = "theme";

export function useTheme() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "dark") {
      setDark(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  function toggleTheme() {
    if (dark) {
      document.documentElement.classList.remove("dark");
      localStorage.setItem(STORAGE_KEY, "light");
    } else {
      document.documentElement.classList.add("dark");
      localStorage.setItem(STORAGE_KEY, "dark");
    }
    setDark(!dark);
  }

  return { dark, toggleTheme };
}
