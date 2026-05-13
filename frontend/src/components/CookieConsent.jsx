/**
 * CookieConsent — GDPR/ePrivacy cookie consent banner.
 *
 * Displays a non-intrusive bottom banner on first visit.
 * Consent state is persisted to localStorage so the banner
 * only shows once. Matches the "Warm Editorial Intelligence"
 * design system.
 */
import { useState, useEffect } from "react";

const CONSENT_KEY = "probexr.cookie_consent";

export default function CookieConsent() {
  const [visible, setVisible] = useState(false);
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    try {
      if (!localStorage.getItem(CONSENT_KEY)) {
        // Small delay so it doesn't flash on load
        const t = setTimeout(() => setVisible(true), 1200);
        return () => clearTimeout(t);
      }
    } catch {
      /* SSR / incognito — ignore */
    }
  }, []);

  function handleAccept() {
    setExiting(true);
    try { localStorage.setItem(CONSENT_KEY, "accepted"); } catch { /* ignore */ }
    setTimeout(() => setVisible(false), 300);
  }

  function handleDecline() {
    setExiting(true);
    try { localStorage.setItem(CONSENT_KEY, "declined"); } catch { /* ignore */ }
    setTimeout(() => setVisible(false), 300);
  }

  if (!visible) return null;

  return (
    <div
      id="cookie-consent-banner"
      role="dialog"
      aria-label="Cookie consent"
      style={{
        position: "fixed",
        bottom: 24,
        left: "50%",
        transform: `translateX(-50%)${exiting ? " translateY(20px)" : ""}`,
        zIndex: 9999,
        width: "min(560px, calc(100vw - 48px))",
        background: "var(--bg-elevated)",
        border: "1px solid var(--border-dim)",
        borderRadius: "var(--radius-card)",
        padding: "20px 24px",
        boxShadow: "var(--shadow-lift)",
        display: "flex",
        flexDirection: "column",
        gap: 14,
        opacity: exiting ? 0 : 1,
        transition: "all 300ms var(--ease)",
        animation: "cookieBannerIn 400ms var(--spring) forwards",
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
        <span style={{ fontSize: 20, lineHeight: 1 }}>🍪</span>
        <div style={{ flex: 1 }}>
          <p
            className="font-body"
            style={{
              fontSize: 13,
              lineHeight: 1.5,
              color: "var(--ink-secondary)",
              margin: 0,
            }}
          >
            We use essential cookies to keep PROBEXR working and optional
            analytics cookies to improve the experience.{" "}
            <a
              href="/PRIVACY_POLICY.md"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                color: "var(--amber)",
                textDecoration: "underline",
                textUnderlineOffset: 2,
              }}
            >
              Privacy Policy
            </a>
          </p>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
        <button
          id="cookie-decline-btn"
          onClick={handleDecline}
          style={{
            padding: "8px 16px",
            fontSize: 13,
            fontFamily: "'Cabinet Grotesk', sans-serif",
            fontWeight: 500,
            color: "var(--ink-tertiary)",
            background: "transparent",
            border: "1px solid var(--border-dim)",
            borderRadius: "var(--radius-btn)",
            cursor: "pointer",
            transition: "all var(--dur-fast) var(--ease)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = "var(--ink-tertiary)";
            e.currentTarget.style.color = "var(--ink-secondary)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = "var(--border-dim)";
            e.currentTarget.style.color = "var(--ink-tertiary)";
          }}
        >
          Decline
        </button>
        <button
          id="cookie-accept-btn"
          onClick={handleAccept}
          style={{
            padding: "8px 20px",
            fontSize: 13,
            fontFamily: "'Cabinet Grotesk', sans-serif",
            fontWeight: 600,
            color: "#fff",
            background: "var(--gradient-cta)",
            border: "none",
            borderRadius: "var(--radius-btn)",
            cursor: "pointer",
            transition: "all var(--dur-fast) var(--ease)",
            boxShadow: "0 2px 8px rgba(232,150,12,0.25)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "translateY(-1px)";
            e.currentTarget.style.boxShadow = "0 4px 16px rgba(232,150,12,0.35)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "translateY(0)";
            e.currentTarget.style.boxShadow = "0 2px 8px rgba(232,150,12,0.25)";
          }}
        >
          Accept
        </button>
      </div>
    </div>
  );
}
