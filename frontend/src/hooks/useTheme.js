/**
 * Theme state and persistence — keeps App thin. Add other app-wide hooks here.
 */
import { useEffect, useState } from "react";

const STORAGE_KEY = "theme";

export function useTheme() {
  const [dark, setDark] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem(STORAGE_KEY) === "dark";
    }
    return false;
  });

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [dark]);

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
