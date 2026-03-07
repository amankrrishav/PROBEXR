import { useState } from "react";

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
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [prevOpen, setPrevOpen] = useState(open);
  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) {
      setEmail("");
      setPassword("");
    }
  }

  if (!open) return null;

  const isSignup = mode === "signup";

  async function handleSubmit(e) {
    e.preventDefault();
    const payload = { email: email.trim(), password };
    const fn = isSignup ? onRegister : onLogin;
    try {
      await fn(payload);
      if (onSuccess) {
        onSuccess(isSignup ? "Account created. You are now logged in." : "Logged in successfully.");
      }
      onClose();
    } catch {
      // error is handled via error prop
    }
  }

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
              {isSignup ? "Create your ReadPulse account" : "Welcome back"}
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
            onClick={() => onModeChange("signup")}
            className={`flex-1 rounded-full px-3 py-1 transition ${
              isSignup
                ? "bg-black text-white dark:bg-white dark:text-black shadow-sm"
                : "text-gray-500 dark:text-gray-400"
            }`}
          >
            Sign up
          </button>
          <button
            type="button"
            onClick={() => onModeChange("login")}
            className={`flex-1 rounded-full px-3 py-1 transition ${
              !isSignup
                ? "bg-black text-white dark:bg-white dark:text-black shadow-sm"
                : "text-gray-500 dark:text-gray-400"
            }`}
          >
            Log in
          </button>
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

          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-gray-300">
              Password
            </label>
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

          {error && (
            <p className="text-[11px] text-red-500">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="mt-1 inline-flex w-full items-center justify-center rounded-full bg-black px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70 dark:bg-white dark:text-black"
          >
            {submitting ? (isSignup ? "Creating account…" : "Signing in…") : isSignup ? "Sign up" : "Log in"}
          </button>

          <p className="mt-1 text-[10px] text-gray-400">
            By continuing you agree to keep your summaries within reasonable use. Perfect for
            testing ideas before scale.
          </p>
        </form>
      </div>
    </div>
  );
}

