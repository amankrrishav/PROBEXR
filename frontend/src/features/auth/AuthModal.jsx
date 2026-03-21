import { useState } from "react";
import { config } from "../../config.js";
import {
  requestMagicLink,
  forgotPassword as forgotPasswordApi,
  resetPassword as resetPasswordApi,
  resendVerification as resendVerificationApi,
} from "../../services/auth.js";

/* ── Shared styles ── */
const S = {
  overlay: {
    position: "fixed", inset: 0, zIndex: 200,
    display: "flex", alignItems: "center", justifyContent: "center",
    background: "rgba(11, 9, 6, 0.7)", backdropFilter: "blur(6px)",
  },
  modal: {
    position: "relative", width: "100%", maxWidth: 440,
    borderRadius: "var(--radius-card)", padding: 28,
    background: "var(--bg-surface)", border: "1px solid var(--border-dim)",
    boxShadow: "var(--shadow-modal)", color: "var(--ink-primary)",
  },
  escBtn: {
    position: "absolute", right: 16, top: 16,
    background: "none", border: "none", cursor: "pointer",
    fontSize: 11, color: "var(--ink-tertiary)",
  },
  title: { fontSize: 18, fontWeight: 600, letterSpacing: "-0.01em" },
  subtitle: { fontSize: 12, color: "var(--ink-secondary)", marginTop: 4 },
  label: { display: "block", fontSize: 12, fontWeight: 500, color: "var(--ink-secondary)", marginBottom: 4 },
  input: {
    width: "100%", padding: "10px 14px", fontSize: 14,
    borderRadius: "var(--radius-input)",
    border: "1px solid var(--border-dim)", background: "var(--bg-input)",
    color: "var(--ink-primary)", outline: "none",
    transition: "border-color var(--dur-fast) var(--ease)",
  },
  primaryBtn: {
    width: "100%", padding: "11px 0", fontSize: 14, fontWeight: 600,
    borderRadius: 999, border: "none", cursor: "pointer",
    background: "var(--gradient-cta)", color: "#fff",
    boxShadow: "var(--shadow-sm)",
    transition: "opacity var(--dur-fast) var(--ease)",
  },
  linkBtn: {
    background: "none", border: "none", cursor: "pointer",
    fontSize: 11, color: "var(--ink-tertiary)",
    textDecoration: "underline", textUnderlineOffset: 2,
  },
  error: { fontSize: 12, color: "var(--rose)", marginBottom: 8 },
  divider: {
    display: "flex", alignItems: "center", gap: 12, margin: "20px 0",
  },
  dividerLine: { flex: 1, height: 1, background: "var(--border-dim)" },
  dividerText: { fontSize: 10, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--ink-tertiary)" },
  socialBtn: {
    flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
    padding: "10px 0", fontSize: 12, fontWeight: 500,
    borderRadius: "var(--radius-btn)", cursor: "pointer",
    border: "1px solid var(--border-dim)", background: "var(--bg-elevated)",
    color: "var(--ink-primary)",
    transition: "border-color var(--dur-fast) var(--ease), background var(--dur-fast) var(--ease)",
  },
  tabs: {
    display: "flex", borderRadius: 999, padding: 3,
    background: "var(--bg-elevated)", marginBottom: 20,
  },
  tab: (active) => ({
    flex: 1, textAlign: "center", padding: "7px 0", fontSize: 13, fontWeight: 500,
    borderRadius: 999, border: "none", cursor: "pointer",
    background: active ? "var(--amber)" : "transparent",
    color: active ? "#fff" : "var(--ink-secondary)",
    transition: "all var(--dur-fast) var(--ease)",
  }),
};

/* ── Password strength ── */
const SPECIAL = new Set("!@#$%^&*()_+-=[]{}|;:',.<>?/~`\"\\");

function PasswordStrengthHint({ password }) {
  const rules = [
    { label: "12+ characters", ok: password.length >= 12 },
    { label: "Uppercase", ok: /[A-Z]/.test(password) },
    { label: "Lowercase", ok: /[a-z]/.test(password) },
    { label: "Digit", ok: /[0-9]/.test(password) },
    { label: "Special", ok: [...password].some(c => SPECIAL.has(c)) },
  ];
  const passed = rules.filter(r => r.ok).length;
  const allGood = passed === rules.length;

  return (
    <div style={{ marginTop: 6 }}>
      <div style={{ display: "flex", gap: 3, marginBottom: 4 }}>
        {rules.map((_, i) => (
          <div key={i} style={{
            height: 3, flex: 1, borderRadius: 2,
            background: i < passed
              ? allGood ? "var(--sage)" : "var(--amber)"
              : "var(--border-dim)",
            transition: "background var(--dur-fast) var(--ease)",
          }} />
        ))}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "2px 10px" }}>
        {rules.map(r => (
          <span key={r.label} style={{
            fontSize: 10,
            color: r.ok ? "var(--sage)" : "var(--ink-tertiary)",
          }}>
            {r.ok ? "✓" : "·"} {r.label}
          </span>
        ))}
      </div>
    </div>
  );
}

/* ── Main Component ── */
export default function AuthModal({
  open, mode, onModeChange, onClose,
  onLogin, onRegister, submitting, error, onSuccess, user,
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [useMagicLink, setUseMagicLink] = useState(false);
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
      setEmail(""); setPassword(""); setUseMagicLink(false);
      setView(mode === "signup" ? "signup" : "login");
      setLocalError(null); setResetToken(""); setNewPassword("");
    }
  }

  const [prevMode, setPrevMode] = useState(mode);
  if (mode !== prevMode) {
    setPrevMode(mode);
    if (view === "login" || view === "signup") {
      setView(mode === "signup" ? "signup" : "login");
    }
  }

  const activeError = localError || error;
  const isSubmitting = localSubmitting || submitting;
  const isSignup = view === "signup";

  /* ── Handlers ── */
  async function handleResendVerification() {
    if (resendCooldown || !user?.email) return;
    setLocalSubmitting(true);
    try {
      await resendVerificationApi(user.email);
      onSuccess?.("Verification email resent! Check your inbox.");
      setResendCooldown(true);
      setTimeout(() => setResendCooldown(false), 60000);
    } catch {
      setLocalError("Failed to resend. Please try again.");
    } finally {
      setLocalSubmitting(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLocalError(null);

    if (view === "forgot") {
      setLocalSubmitting(true);
      try {
        await forgotPasswordApi(email.trim());
        onSuccess?.("If that email exists, a reset link has been sent.");
        onClose();
      } catch { setLocalError("Something went wrong. Please try again."); }
      finally { setLocalSubmitting(false); }
      return;
    }

    if (view === "reset") {
      setLocalSubmitting(true);
      try {
        await resetPasswordApi(resetToken.trim(), newPassword);
        onSuccess?.("Password updated. Please log in with your new password.");
        setView("login"); onModeChange("login");
        setResetToken(""); setNewPassword("");
      } catch (err) { setLocalError(err.message || "Reset failed. Link may have expired."); }
      finally { setLocalSubmitting(false); }
      return;
    }

    if (useMagicLink) {
      setLocalSubmitting(true);
      try {
        await requestMagicLink(email.trim());
        onSuccess?.("Magic link sent! Check your inbox.");
        onClose();
      } catch { setLocalError("Failed to send magic link. Please try again."); }
      finally { setLocalSubmitting(false); }
      return;
    }

    const payload = { email: email.trim(), password };
    try {
      await (isSignup ? onRegister : onLogin)(payload);
      onSuccess?.(isSignup ? "Account created!" : "Logged in!");
      onClose();
    } catch { /* error via prop */ }
  }

  /* ── Unverified banner ── */
  if (open && user && !user.is_verified) {
    return (
      <div style={S.overlay}>
        <div style={S.modal}>
          <button type="button" onClick={onClose} style={S.escBtn}>Esc</button>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
            <div style={{
              width: 40, height: 40, borderRadius: "50%",
              background: "var(--amber-dim)", display: "flex",
              alignItems: "center", justifyContent: "center", fontSize: 18,
            }}>⚠</div>
            <div>
              <div style={S.title}>Verify your email</div>
              <div style={S.subtitle}>Required to use all features</div>
            </div>
          </div>
          <p style={{ fontSize: 13, color: "var(--ink-secondary)", marginBottom: 20 }}>
            We sent a verification link to <strong style={{ color: "var(--ink-primary)" }}>{user.email}</strong>.
            Click the link to unlock full access.
          </p>
          {activeError && <p style={S.error}>{activeError}</p>}
          <button
            type="button" onClick={handleResendVerification}
            disabled={isSubmitting || resendCooldown}
            style={{ ...S.primaryBtn, opacity: (isSubmitting || resendCooldown) ? 0.6 : 1 }}
          >
            {localSubmitting ? "Sending…" : resendCooldown ? "Link sent — check inbox" : "Resend verification email"}
          </button>
          <p style={{ textAlign: "center", fontSize: 10, color: "var(--ink-tertiary)", marginTop: 12 }}>
            Check your spam folder if you don't see it.
          </p>
        </div>
      </div>
    );
  }

  if (!open) return null;

  /* ── Forgot password ── */
  if (view === "forgot") {
    return (
      <div style={S.overlay}>
        <div style={S.modal}>
          <button type="button" onClick={onClose} style={S.escBtn}>Esc</button>
          <div style={{ ...S.title, marginBottom: 4 }}>Reset your password</div>
          <p style={{ ...S.subtitle, marginBottom: 20 }}>Enter your email and we'll send a reset link.</p>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 12 }}>
              <label style={S.label}>Email</label>
              <input type="email" autoComplete="email" required value={email}
                onChange={e => setEmail(e.target.value)} style={S.input} placeholder="you@company.com" />
            </div>
            {activeError && <p style={S.error}>{activeError}</p>}
            <button type="submit" disabled={isSubmitting}
              style={{ ...S.primaryBtn, opacity: isSubmitting ? 0.6 : 1, marginBottom: 12 }}>
              {isSubmitting ? "Sending…" : "Send reset link"}
            </button>
            <div style={{ textAlign: "center" }}>
              <button type="button" onClick={() => { setView("login"); onModeChange("login"); setLocalError(null); }} style={S.linkBtn}>
                Back to log in
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  /* ── Reset password ── */
  if (view === "reset") {
    return (
      <div style={S.overlay}>
        <div style={S.modal}>
          <button type="button" onClick={onClose} style={S.escBtn}>Esc</button>
          <div style={{ ...S.title, marginBottom: 4 }}>Set new password</div>
          <p style={{ ...S.subtitle, marginBottom: 20 }}>Paste your reset token and choose a new password.</p>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 12 }}>
              <label style={S.label}>Reset token</label>
              <input type="text" required value={resetToken}
                onChange={e => setResetToken(e.target.value)}
                style={{ ...S.input, fontFamily: "'Commit Mono', monospace" }}
                placeholder="Paste token from email" />
            </div>
            <div style={{ marginBottom: 12 }}>
              <label style={S.label}>New password</label>
              <input type="password" autoComplete="new-password" required minLength={12}
                value={newPassword} onChange={e => setNewPassword(e.target.value)}
                style={S.input} placeholder="12+ chars, upper, lower, digit, symbol" />
            </div>
            {activeError && <p style={S.error}>{activeError}</p>}
            <button type="submit" disabled={isSubmitting}
              style={{ ...S.primaryBtn, opacity: isSubmitting ? 0.6 : 1, marginBottom: 12 }}>
              {isSubmitting ? "Updating…" : "Update password"}
            </button>
            <div style={{ textAlign: "center" }}>
              <button type="button" onClick={() => { setView("login"); onModeChange("login"); setLocalError(null); }} style={S.linkBtn}>
                Back to log in
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  /* ── Login / Signup ── */
  return (
    <div style={S.overlay}>
      <div style={S.modal}>
        <button type="button" onClick={onClose} style={S.escBtn}>Esc</button>

        {/* Header */}
        <div style={{ marginBottom: 20 }}>
          <div style={S.title}>
            {isSignup ? "Create your PROBEXR account" : "Welcome back"}
          </div>
          <p style={S.subtitle}>One account for all your summaries. No clutter.</p>
        </div>

        {/* Tabs */}
        <div style={S.tabs}>
          <button type="button" onClick={() => { onModeChange("signup"); setView("signup"); setLocalError(null); }}
            style={S.tab(isSignup)}>Sign up</button>
          <button type="button" onClick={() => { onModeChange("login"); setView("login"); setLocalError(null); }}
            style={S.tab(!isSignup)}>Log in</button>
        </div>

        {/* Social Buttons */}
        <div style={{ display: "flex", gap: 12, marginBottom: 0 }}>
          <button type="button"
            onClick={() => window.location.href = `${config.apiBaseUrl}/auth/google/login`}
            style={S.socialBtn}
            onMouseEnter={e => e.currentTarget.style.borderColor = "var(--amber)"}
            onMouseLeave={e => e.currentTarget.style.borderColor = "var(--border-dim)"}
          >
            <svg style={{ width: 16, height: 16 }} viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            Google
          </button>
          <button type="button"
            onClick={() => window.location.href = `${config.apiBaseUrl}/auth/github/login`}
            style={S.socialBtn}
            onMouseEnter={e => e.currentTarget.style.borderColor = "var(--amber)"}
            onMouseLeave={e => e.currentTarget.style.borderColor = "var(--border-dim)"}
          >
            <svg style={{ width: 16, height: 16 }} fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
            </svg>
            GitHub
          </button>
        </div>

        {/* Divider */}
        <div style={S.divider}>
          <div style={S.dividerLine} />
          <span style={S.dividerText}>or continue with email</span>
          <div style={S.dividerLine} />
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 12 }}>
            <label style={S.label}>Email</label>
            <input type="email" autoComplete="email" required value={email}
              onChange={e => setEmail(e.target.value)} style={S.input}
              placeholder="you@company.com" />
          </div>

          {!useMagicLink && (
            <div style={{ marginBottom: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <label style={S.label}>Password</label>
                {!isSignup && (
                  <button type="button"
                    onClick={() => { setView("forgot"); setLocalError(null); }}
                    style={{ ...S.linkBtn, marginBottom: 4 }}>
                    Forgot password?
                  </button>
                )}
              </div>
              <input type="password"
                autoComplete={isSignup ? "new-password" : "current-password"}
                required minLength={12} value={password}
                onChange={e => setPassword(e.target.value)} style={S.input}
                placeholder={isSignup ? "12+ chars, upper, lower, digit, symbol" : "Your password"} />
              {isSignup && password.length > 0 && <PasswordStrengthHint password={password} />}
            </div>
          )}

          {activeError && <p style={S.error}>{activeError}</p>}

          <button type="submit" disabled={isSubmitting}
            style={{ ...S.primaryBtn, opacity: isSubmitting ? 0.6 : 1, marginBottom: 12 }}>
            {isSubmitting
              ? (isSignup ? "Creating account…" : "Signing in…")
              : useMagicLink ? "Send login link" : isSignup ? "Sign up" : "Log in"}
          </button>

          <div style={{ textAlign: "center", marginBottom: 8 }}>
            <button type="button" onClick={() => setUseMagicLink(!useMagicLink)} style={S.linkBtn}>
              {useMagicLink ? "Use password instead" : "Email me a login link instead"}
            </button>
          </div>

          <p style={{ fontSize: 10, color: "var(--ink-tertiary)", textAlign: "center" }}>
            By continuing you agree to keep your summaries within reasonable use.
          </p>
        </form>
      </div>
    </div>
  );
}