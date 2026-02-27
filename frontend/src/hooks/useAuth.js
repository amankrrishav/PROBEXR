import { useEffect, useState } from "react";
import { getCurrentUser, login as loginApi, register as registerApi, upgradeDemoPro, logout as logoutApi } from "../services/auth.js";

export function useAuth() {
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getCurrentUser()
      .then((u) => {
        if (!cancelled) {
          setUser(u);
          setError(null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setUser(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setInitializing(false);
        }
      });

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

  async function upgradeToDemoPro() {
    setError(null);
    setSubmitting(true);
    try {
      const updated = await upgradeDemoPro();
      setUser(updated);
      return updated;
    } catch (err) {
      setError(err.message || "Upgrade failed. Please try again later.");
      throw err;
    } finally {
      setSubmitting(false);
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
    upgradeToDemoPro,
  };
}

