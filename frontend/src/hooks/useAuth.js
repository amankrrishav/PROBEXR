import { useEffect, useState } from "react";
import { getCurrentUser, login as loginApi, register as registerApi, logout as logoutApi, logoutAll as logoutAllApi, refreshToken } from "../services/auth.js";

export function useAuth() {
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        const u = await getCurrentUser();
        if (!cancelled) {
          setUser(u);
          setError(null);
        }
      } catch {
        // Access token may be expired — try refreshing
        if (!cancelled) {
          try {
            await refreshToken();
            const u = await getCurrentUser();
            if (!cancelled) {
              setUser(u);
              setError(null);
            }
          } catch {
            if (!cancelled) setUser(null);
          }
        }
      } finally {
        if (!cancelled) setInitializing(false);
      }
    }

    init();

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleAuth(apiFn, { email, password }) {
    setError(null);
    setSubmitting(true);
    try {
      await apiFn({ email, password });
      const me = await getCurrentUser();
      setUser(me);
      return me;
    } catch (err) {
      setError(err.message || "Authentication failed. Please try again.");
      throw err;
    } finally {
      setSubmitting(false);
    }
  }

  function login(credentials) {
    return handleAuth(loginApi, credentials);
  }

  function register(credentials) {
    return handleAuth(registerApi, credentials);
  }

  async function logout() {
    try {
      await logoutApi();
    } catch (err) {
      console.error("Logout failed", err);
    } finally {
      setUser(null);
    }
  }

  async function logoutAll() {
    try {
      await logoutAllApi();
    } catch (err) {
      console.error("Logout all failed", err);
    } finally {
      setUser(null);
    }
  }

  return {
    user,
    initializing,
    submitting,
    error,
    setError,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    logoutAll,
  };
}
