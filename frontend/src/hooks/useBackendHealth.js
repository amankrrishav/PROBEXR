/**
 * Backend health — call GET / on load. Use for status, mode (extractive vs groq), version.
 */
import { useEffect, useState } from "react";
import { getHealth } from "../services/api.js";

export function useBackendHealth(options = {}) {
  const { enabled = true } = options;
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(enabled);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    getHealth()
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setData(null);
          setError(err.message || "Backend unreachable");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [enabled]);

  return {
    backend: data,
    backendMode: data?.mode ?? null,
    backendVersion: data?.version ?? null,
    backendError: error,
    backendLoading: loading,
  };
}
