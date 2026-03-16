import { useState } from "react";
import { config } from "../../config";

export default function AuthModal({
  open,
  mode,
  onModeChange,
  onClose,
  onLogin,
  onRegister,
  submitting,
  error,
  onSuccess,
  // Pass the logged-in user so we can show the unverified banner
  user,
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [useMagicLink, setUseMagicLink] = useState(false);

  // "login" | "signup" | "forgot" | "reset"
  const [view, setView] = useState(mode === "signup" ? "signup" : "login");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [localError, setLocalError] = useState(null);
  const [localSubmitting, setLocalSubmitting] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(false);

  const [prevOpen, setPrevOpen] = useState(open);
  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) {
      setEmail("");
      setPassword("");
      setUseMagicLink(false);
      setView(mode === "signup" ? "signup" : "login");
      setLocalError(null);
      setResetToken("");
      setNewPassword("");
    }
  }

  // Sync view with external mode changes
  const [prevMode, setPrevMode] = useState(mode);
  if (mode !== prevMode) {
    setPrevMode(mode);
    if (view === "login" || view === "signup") {
      setView(mode === "signup" ? "signup" : "login");
    }
  }

  async function handleResendVerification() {
    if (resendCooldown || !user?.email) return;
    setLocalSubmitting(true);
    try {
      await fetch(`${config.apiBaseUrl}/auth/resend-verification`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: user.email }),
      });
      onSuccess?.("Verification email resent! Check your inbox.");
      setResendCooldown(true);
      setTimeout(() => setResendCooldown(false), 60000);
    } catch {
      setLocalError("Failed to resend. Please try again.");
    } finally {
      setLocalSubmitting(false);
    }
  }

  // Unverified banner — shown when logged in but email not verified
  if (open && user && !user.is_verified) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
        <div className="relative w-full max-w-md rounded-2xl bg-white/95 p-6 shadow-2xl dark:bg-[#111111]/95 border border-gray-200 dark:border-gray-800">
          <button type="button" onClick={onClose} className="absolute right-4 top-4 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">Esc</button>
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/30">
              <svg className="h-5 w-5 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
              </svg>
            </div>
            <div>
              <h2 className="text-base font-semibold tracking-tight">Verify your email</h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">Required to use all features</p>
            </div>
          </div>
          <p className="mb-5 text-sm text-gray-600 dark:text-gray-300">
            We sent a verification link to <span className="font-medium text-black dark:text-white">{user.email}</span>. Click the link in that email to unlock full access.
          </p>
          {localError && <p className="mb-3 text-[11px] text-red-500">{localError}</p>}
          <button
            type="button"
            onClick={handleResendVerification}
            disabled={localSubmitting || resendCooldown}
            className="inline-flex w-full items-center justify-center rounded-full bg-black px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70 dark:bg-white dark:text-black"
          >
            {localSubmitting ? "Sending…" : resendCooldown ? "Link sent — check your inbox" : "Resend verification email"}
          </button>
          <p className="mt-3 text-center text-[10px] text-gray-400">
            Check your spam folder if you don't see it.
          </p>
        </div>
      </div>
    );
  }

  if (!open) return null;

  const isSignup = view === "signup";
  const activeError = localError || error;
  const isSubmitting = localSubmitting || submitting;

  async function handleSubmit(e) {
    e.preventDefault();
    setLocalError(null);

    if (view === "forgot") {
      setLocalSubmitting(true);
      try {
        const resp = await fetch(`${config.apiBaseUrl}/auth/forgot-password`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: email.trim() }),
        });
        if (!resp.ok) throw new Error("Request failed");
        onSuccess?.("If that email exists, a reset link has been sent.");
        onClose();
      } catch {
        setLocalError("Something went wrong. Please try again.");
      } finally {
        setLocalSubmitting(false);
      }
      return;
    }

    if (view === "reset") {
      setLocalSubmitting(true);
      try {
        const resp = await fetch(`${config.apiBaseUrl}/auth/reset-password`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token: resetToken.trim(), new_password: newPassword }),
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || "Reset failed");
        onSuccess?.("Password updated. Please log in with your new password.");
        setView("login");
        onModeChange("login");
        setResetToken("");
        setNewPassword("");
      } catch (err) {
        setLocalError(err.message);
      } finally {
        setLocalSubmitting(false);
      }
      return;
    }

    if (useMagicLink) {
      setLocalSubmitting(true);
      try {
        const resp = await fetch(`${config.apiBaseUrl}/auth/magic-link`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: email.trim() }),
        });
        if (!resp.ok) throw new Error("Failed to send link");
        onSuccess?.("Magic link sent! Check server logs if locally developing.");
        onClose();
      } catch {
        setLocalError("Failed to send magic link. Please try again.");
      } finally {
        setLocalSubmitting(false);
      }
      return;
    }

    const payload = { email: email.trim(), password };
    const fn = isSignup ? onRegister : onLogin;
    try {
      await fn(payload);
      onSuccess?.(isSignup ? "Account created. You are now logged in." : "Logged in successfully.");
      onClose();
    } catch {
      // error handled via error prop
    }
  }

  // --- Forgot password view ---
  if (view === "forgot") {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
        <div className="relative w-full max-w-md rounded-2xl bg-white/95 p-6 shadow-2xl dark:bg-[#111111]/95 border border-gray-200 dark:border-gray-800">
          <button type="button" onClick={onClose} className="absolute right-4 top-4 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">Esc</button>
          <h2 className="text-lg font-semibold tracking-tight mb-1">Reset your password</h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-6">Enter your email and we'll send a reset link (expires in 30 min).</p>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Email</label>
              <input
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm outline-none ring-0 transition focus:border-black focus:ring-1 focus:ring-black dark:border-gray-700 dark:bg-[#050505] dark:focus:border-white dark:focus:ring-white"
                placeholder="you@company.com"
              />
            </div>
            {activeError && <p className="text-[11px] text-red-500">{activeError}</p>}
            <button type="submit" disabled={isSubmitting} className="mt-1 inline-flex w-full items-center justify-center rounded-full bg-black px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70 dark:bg-white dark:text-black">
              {isSubmitting ? "Sending…" : "Send reset link"}
            </button>
            <div className="flex justify-center">
              <button type="button" onClick={() => { setView("login"); onModeChange("login"); setLocalError(null); }} className="text-[10px] text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 underline underline-offset-2">
                Back to log in
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  // --- Reset password view (arrived via email link) ---
  if (view === "reset") {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
        <div className="relative w-full max-w-md rounded-2xl bg-white/95 p-6 shadow-2xl dark:bg-[#111111]/95 border border-gray-200 dark:border-gray-800">
          <button type="button" onClick={onClose} className="absolute right-4 top-4 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">Esc</button>
          <h2 className="text-lg font-semibold tracking-tight mb-1">Set new password</h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-6">Paste your reset token and choose a new password.</p>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Reset token</label>
              <input
                type="text"
                required
                value={resetToken}
                onChange={(e) => setResetToken(e.target.value)}
                className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm outline-none ring-0 transition focus:border-black focus:ring-1 focus:ring-black dark:border-gray-700 dark:bg-[#050505] dark:focus:border-white dark:focus:ring-white font-mono"
                placeholder="Paste token from email link"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-gray-300">New password</label>
              <input
                type="password"
                autoComplete="new-password"
                required
                minLength={8}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm outline-none ring-0 transition focus:border-black focus:ring-1 focus:ring-black dark:border-gray-700 dark:bg-[#050505] dark:focus:border-white dark:focus:ring-white"
                placeholder="At least 8 characters"
              />
            </div>
            {activeError && <p className="text-[11px] text-red-500">{activeError}</p>}
            <button type="submit" disabled={isSubmitting} className="mt-1 inline-flex w-full items-center justify-center rounded-full bg-black px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70 dark:bg-white dark:text-black">
              {isSubmitting ? "Updating…" : "Update password"}
            </button>
            <div className="flex justify-center">
              <button type="button" onClick={() => { setView("login"); onModeChange("login"); setLocalError(null); }} className="text-[10px] text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 underline underline-offset-2">
                Back to log in
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  // --- Login / Signup view ---
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="relative w-full max-w-md rounded-2xl bg-white/95 p-6 shadow-2xl dark:bg-[#111111]/95 border border-gray-200 dark:border-gray-800">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
        >
          Esc
        </button>

        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">
              {isSignup ? "Create your PROBEXR account" : "Welcome back"}
            </h2>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              One account for all your summaries. No clutter.
            </p>
          </div>

          <div className="inline-flex items-center rounded-full bg-gray-100 px-2 py-1 text-[10px] font-medium text-gray-500 dark:bg-gray-900 dark:text-gray-300">
            <span className="mr-1 h-1.5 w-1.5 rounded-full bg-emerald-400" />
            {isSignup ? "Step 2 · Personalize" : "Fast login"}
          </div>
        </div>

        <div className="mb-4 flex rounded-full bg-gray-100 p-1 text-xs dark:bg-gray-900">
          <button
            type="button"
            onClick={() => { onModeChange("signup"); setView("signup"); setLocalError(null); }}
            className={`flex-1 rounded-full px-3 py-1 transition ${isSignup
                ? "bg-black text-white dark:bg-white dark:text-black shadow-sm"
                : "text-gray-500 dark:text-gray-400"
              }`}
          >
            Sign up
          </button>
          <button
            type="button"
            onClick={() => { onModeChange("login"); setView("login"); setLocalError(null); }}
            className={`flex-1 rounded-full px-3 py-1 transition ${!isSignup
                ? "bg-black text-white dark:bg-white dark:text-black shadow-sm"
                : "text-gray-500 dark:text-gray-400"
              }`}
          >
            Log in
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-6">
          <button
            onClick={() => window.location.href = `${config.apiBaseUrl}/auth/google/login`}
            className="flex items-center justify-center gap-2 rounded-xl border border-gray-200 py-2 text-[11px] font-medium transition hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-white/5"
          >
            <svg className="h-4 w-4" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            Google
          </button>
          <button
            onClick={() => window.location.href = `${config.apiBaseUrl}/auth/github/login`}
            className="flex items-center justify-center gap-2 rounded-xl border border-gray-200 py-2 text-[11px] font-medium transition hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-white/5"
          >
            <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
            </svg>
            GitHub
          </button>
        </div>

        <div className="relative mb-6 flex items-center">
          <div className="flex-grow border-t border-gray-100 dark:border-gray-800" />
          <span className="mx-4 flex-shrink text-[10px] uppercase tracking-wider text-gray-400">
            or continue with email
          </span>
          <div className="flex-grow border-t border-gray-100 dark:border-gray-800" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-gray-300">
              Work email
            </label>
            <input
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm outline-none ring-0 transition focus:border-black focus:ring-1 focus:ring-black dark:border-gray-700 dark:bg-[#050505] dark:focus:border-white dark:focus:ring-white"
              placeholder="you@company.com"
            />
          </div>

          {!useMagicLink && (
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-gray-600 dark:text-gray-300">
                  Password
                </label>
                {!isSignup && (
                  <button
                    type="button"
                    onClick={() => { setView("forgot"); setLocalError(null); }}
                    className="text-[10px] text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 underline underline-offset-2"
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <input
                type="password"
                autoComplete={isSignup ? "new-password" : "current-password"}
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm outline-none ring-0 transition focus:border-black focus:ring-1 focus:ring-black dark:border-gray-700 dark:bg-[#050505] dark:focus:border-white dark:focus:ring-white"
                placeholder="At least 8 characters"
              />
            </div>
          )}

          {activeError && (
            <p className="text-[11px] text-red-500">{activeError}</p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-1 inline-flex w-full items-center justify-center rounded-full bg-black px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70 dark:bg-white dark:text-black"
          >
            {isSubmitting ? (isSignup ? "Creating account…" : "Signing in…") : useMagicLink ? "Send login link" : isSignup ? "Sign up" : "Log in"}
          </button>

          <div className="flex justify-center">
            <button
              type="button"
              onClick={() => setUseMagicLink(!useMagicLink)}
              className="text-[10px] text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 underline underline-offset-2"
            >
              {useMagicLink ? "Use password instead" : "Email me a login link instead"}
            </button>
          </div>

          <p className="mt-1 text-[10px] text-gray-400">
            By continuing you agree to keep your summaries within reasonable use. Perfect for
            testing ideas before scale.
          </p>
        </form>
      </div>
    </div>
  );
}
