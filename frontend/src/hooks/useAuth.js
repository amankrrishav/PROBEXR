import { useEffect, useState } from "react";
import { getCurrentUser, login as loginApi, register as registerApi, upgradeDemoPro } from "../services/auth.js";
import { clearAccessToken, getAccessToken, setAccessToken } from "../services/authStorage.js";

export function useAuth() {
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setInitializing(false);
      return;
    }

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
          clearAccessToken();
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
      const data = await apiFn({ email, password });
      const token = data?.access_token;
      if (token) {
        setAccessToken(token);
      }
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

  function logout() {
    clearAccessToken();
    setUser(null);
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

