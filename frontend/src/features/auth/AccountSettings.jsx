/**
 * AccountSettings — Modal rendered via React portal into document.body.
 * A1: Proper overlay isolation, focus trap, Escape/click close, scale+fade animation.
 * A3: Dev notes removed, URL validation, read-only email with lock icon, feature flags.
 * A4: Live 40×40 avatar preview with debounce, loading spinner, clear button, fallback.
 * B12: Validates on save, persists to localStorage, shows success toast.
 */
import { useState, useEffect, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { useAppContext } from "../../contexts/AppContext";
import { useFeatureFlags } from "../../hooks/useFeatureFlags";

const USER_STORAGE_KEY = "probexr_user";

function loadSavedUser() {
  try {
    const raw = localStorage.getItem(USER_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveUser(data) {
  try {
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(data));
  } catch { /* ignore */ }
}

function isValidUrl(str) {
  if (!str || !str.trim()) return true; // empty is valid
  try {
    new URL(str);
    return true;
  } catch {
    return false;
  }
}

function getInitials(name, email) {
  if (name) return name.charAt(0).toUpperCase();
  if (email) return email.charAt(0).toUpperCase();
  return "?";
}

export default function AccountSettings({ open, onClose }) {
  const { auth } = useAppContext();
  const { user } = auth;
  const features = useFeatureFlags();

  const [fullName, setFullName] = useState(user?.full_name || "");
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || "");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState(null);

  // Validation
  const [nameError, setNameError] = useState(null);
  const [urlError, setUrlError] = useState(null);
  const [shakeField, setShakeField] = useState(null);

  // Avatar preview
  const [previewUrl, setPreviewUrl] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState(false);

  // Animation
  const [visible, setVisible] = useState(false);
  const [closing, setClosing] = useState(false);

  // Focus trap
  const modalRef = useRef(null);
  const firstFocusRef = useRef(null);

  // Hydrate from localStorage on mount
  useEffect(() => {
    const saved = loadSavedUser();
    if (saved) {
      if (!user?.full_name && saved.full_name) setFullName(saved.full_name);
      if (!user?.avatar_url && saved.avatar_url) setAvatarUrl(saved.avatar_url);
    }
  }, [user]);

  // Open animation
  useEffect(() => {
    if (open) {
      setVisible(true);
      setClosing(false);
      // Reset state
      setMessage(null);
      setNameError(null);
      setUrlError(null);
      setShakeField(null);
      // Focus first input after render
      requestAnimationFrame(() => {
        firstFocusRef.current?.focus();
      });
    }
  }, [open]);

  // Debounced avatar preview
  useEffect(() => {
    if (!avatarUrl.trim()) {
      setPreviewUrl("");
      setPreviewError(false);
      return;
    }
    setPreviewLoading(true);
    setPreviewError(false);
    const timer = setTimeout(() => {
      if (isValidUrl(avatarUrl)) {
        setPreviewUrl(avatarUrl);
      } else {
        setPreviewUrl("");
        setPreviewLoading(false);
      }
    }, 600);
    return () => clearTimeout(timer);
  }, [avatarUrl]);

  const handleClose = useCallback(() => {
    setClosing(true);
    setTimeout(() => {
      setVisible(false);
      setClosing(false);
      onClose();
    }, 150);
  }, [onClose]);

  // Focus trap
  useEffect(() => {
    if (!open || !visible) return;
    function handleKeyDown(e) {
      if (e.key === "Escape") {
        e.preventDefault();
        handleClose();
        return;
      }
      if (e.key === "Tab") {
        const modal = modalRef.current;
        if (!modal) return;
        const focusable = modal.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey) {
          if (document.activeElement === first) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, visible, handleClose]);

  if (!open && !visible) return null;

  const fallbackAvatar = `https://ui-avatars.com/api/?name=${encodeURIComponent(fullName || user?.email || "U")}&background=E8960C&color=0B0906&size=80&bold=true`;

  async function handleUpdate(e) {
    e.preventDefault();
    setNameError(null);
    setUrlError(null);
    setShakeField(null);

    // Validate
    if (!fullName.trim()) {
      setNameError("Full name is required.");
      setShakeField("name");
      setTimeout(() => setShakeField(null), 500);
      return;
    }
    if (avatarUrl.trim() && !isValidUrl(avatarUrl)) {
      setUrlError("Must be a valid URL.");
      setShakeField("avatar");
      setTimeout(() => setShakeField(null), 500);
      return;
    }

    setSubmitting(true);
    setMessage(null);
    try {
      // Try backend update first
      await auth.updateProfile({
        full_name: fullName.trim() || null,
        avatar_url: avatarUrl.trim() || null,
      });
    } catch {
      // Backend might be down, still save locally
    }

    // Always persist to localStorage
    saveUser({
      full_name: fullName.trim(),
      avatar_url: avatarUrl.trim(),
      email: user?.email || "",
    });

    setSubmitting(false);
    setMessage({ type: "success", text: "Changes saved" });
    setTimeout(() => handleClose(), 2500);
  }

  function handleClearAvatar() {
    setAvatarUrl("");
    setPreviewUrl("");
    setPreviewError(false);
    setUrlError(null);
  }

  function handleAvatarBlur() {
    if (avatarUrl.trim() && !isValidUrl(avatarUrl)) {
      setUrlError("Must be a valid URL.");
    } else {
      setUrlError(null);
    }
  }

  const modalContent = (
    <div
      className="account-settings-backdrop"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(0,0,0,0.4)",
        backdropFilter: "blur(4px)",
        WebkitBackdropFilter: "blur(4px)",
        opacity: closing ? 0 : 1,
        transition: "opacity 150ms ease",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) handleClose();
      }}
    >
      <div
        ref={modalRef}
        className="account-settings-card"
        style={{
          position: "relative",
          width: "100%",
          maxWidth: 420,
          margin: "0 16px",
          borderRadius: 16,
          background: "var(--bg-surface)",
          border: "1px solid var(--border-dim)",
          padding: 24,
          boxShadow: "var(--shadow-modal)",
          transform: closing ? "scale(0.97)" : "scale(1)",
          opacity: closing ? 0 : 1,
          transition: "transform 150ms ease, opacity 150ms ease",
        }}
        role="dialog"
        aria-modal="true"
        aria-label="Account Settings"
      >
        {/* Close button */}
        <button
          type="button"
          onClick={handleClose}
          style={{
            position: "absolute",
            right: 16,
            top: 16,
            width: 28,
            height: 28,
            borderRadius: 6,
            border: "none",
            background: "transparent",
            color: "var(--ink-tertiary)",
            fontSize: 16,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 150ms ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "var(--bg-elevated)";
            e.currentTarget.style.color = "var(--ink-primary)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
            e.currentTarget.style.color = "var(--ink-tertiary)";
          }}
          aria-label="Close"
        >
          ×
        </button>

        <h2 className="font-body" style={{
          fontSize: 18, fontWeight: 600, color: "var(--ink-primary)",
          marginBottom: 20, letterSpacing: "-0.01em",
        }}>
          Account Settings
        </h2>

        <form onSubmit={handleUpdate}>
          {/* Full Name */}
          <div style={{ marginBottom: 16 }}>
            <label className="font-mono" style={{
              fontSize: 10, fontWeight: 500, textTransform: "uppercase",
              letterSpacing: "0.1em", color: "var(--ink-tertiary)",
              display: "block", marginBottom: 6,
            }}>
              Full Name
            </label>
            <input
              ref={firstFocusRef}
              type="text"
              value={fullName}
              onChange={(e) => { setFullName(e.target.value); setNameError(null); }}
              placeholder="e.g. Jane Doe"
              className="font-body"
              style={{
                width: "100%",
                padding: "10px 14px",
                borderRadius: "var(--radius-input)",
                border: `1px solid ${nameError ? "var(--rose)" : "var(--border-dim)"}`,
                background: "var(--bg-input)",
                color: "var(--ink-primary)",
                fontSize: 14,
                outline: "none",
                transition: "border-color 150ms ease",
                animation: shakeField === "name" ? "shake 400ms ease" : "none",
              }}
              aria-label="Full Name"
            />
            {nameError && (
              <p className="font-mono" style={{ fontSize: 11, color: "var(--rose)", marginTop: 4 }}>
                {nameError}
              </p>
            )}
          </div>

          {/* Avatar URL with preview */}
          <div style={{ marginBottom: 16 }}>
            <label className="font-mono" style={{
              fontSize: 10, fontWeight: 500, textTransform: "uppercase",
              letterSpacing: "0.1em", color: "var(--ink-tertiary)",
              display: "block", marginBottom: 6,
            }}>
              Paste a publicly accessible image URL
            </label>
            <div role="group" aria-label="Avatar image" style={{ display: "flex", alignItems: "center", gap: 12 }}>
              {/* Live preview circle */}
              <div style={{
                width: 40, height: 40, minWidth: 40, borderRadius: "50%",
                overflow: "hidden", border: "1px solid var(--border-dim)",
                background: "var(--bg-elevated)",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                {previewLoading && !previewError && previewUrl ? (
                  <div style={{
                    width: 16, height: 16,
                    border: "2px solid var(--border-lit)",
                    borderTopColor: "var(--amber)",
                    borderRadius: "50%",
                    animation: "spin 600ms linear infinite",
                  }} />
                ) : previewUrl && !previewError ? (
                  <img
                    src={previewUrl}
                    alt="Avatar preview"
                    style={{ width: 40, height: 40, objectFit: "cover" }}
                    onLoad={() => setPreviewLoading(false)}
                    onError={() => { setPreviewError(true); setPreviewLoading(false); }}
                  />
                ) : (
                  <img
                    src={fallbackAvatar}
                    alt="Avatar fallback"
                    style={{ width: 40, height: 40, objectFit: "cover" }}
                  />
                )}
              </div>
              {/* Input + clear */}
              <div style={{ flex: 1, position: "relative" }}>
                <input
                  type="url"
                  value={avatarUrl}
                  onChange={(e) => { setAvatarUrl(e.target.value); setUrlError(null); }}
                  onBlur={handleAvatarBlur}
                  placeholder="https://example.com/avatar.jpg"
                  className="font-body"
                  style={{
                    width: "100%",
                    padding: "10px 32px 10px 14px",
                    borderRadius: "var(--radius-input)",
                    border: `1px solid ${urlError ? "var(--rose)" : "var(--border-dim)"}`,
                    background: "var(--bg-input)",
                    color: "var(--ink-primary)",
                    fontSize: 14,
                    outline: "none",
                    transition: "border-color 150ms ease",
                    animation: shakeField === "avatar" ? "shake 400ms ease" : "none",
                  }}
                  aria-label="Avatar URL"
                />
                {avatarUrl && (
                  <button
                    type="button"
                    onClick={handleClearAvatar}
                    style={{
                      position: "absolute", right: 8, top: "50%",
                      transform: "translateY(-50%)",
                      width: 20, height: 20, borderRadius: "50%",
                      border: "none", background: "var(--bg-elevated)",
                      color: "var(--ink-tertiary)", fontSize: 12,
                      cursor: "pointer", display: "flex",
                      alignItems: "center", justifyContent: "center",
                    }}
                    aria-label="Clear avatar URL"
                  >
                    ×
                  </button>
                )}
              </div>
            </div>
            {urlError && (
              <p className="font-mono" style={{ fontSize: 11, color: "var(--rose)", marginTop: 4 }}>
                {urlError}
              </p>
            )}
          </div>

          {/* Email (read-only) */}
          <div style={{ marginBottom: 20 }}>
            <label className="font-mono" style={{
              fontSize: 10, fontWeight: 500, textTransform: "uppercase",
              letterSpacing: "0.1em", color: "var(--ink-tertiary)",
              display: "block", marginBottom: 6,
            }}>
              Email
            </label>
            <div style={{ position: "relative" }}>
              <input
                type="email"
                disabled
                readOnly
                value={user?.email || ""}
                className="font-body"
                style={{
                  width: "100%",
                  padding: "10px 14px 10px 32px",
                  borderRadius: "var(--radius-input)",
                  border: "1px solid var(--border-dim)",
                  background: "var(--bg-elevated)",
                  color: "var(--ink-tertiary)",
                  fontSize: 14,
                  cursor: "not-allowed",
                  opacity: 0.6,
                }}
                title={features.emailEditing ? "" : "Email editing coming soon"}
                aria-label="Email (read-only)"
              />
              {/* Lock icon */}
              <span style={{
                position: "absolute", left: 10, top: "50%",
                transform: "translateY(-50%)", fontSize: 12,
                color: "var(--ink-tertiary)", pointerEvents: "none",
              }}>
                🔒
              </span>
            </div>
          </div>

          {/* Message */}
          {message && (
            <p className="font-body" style={{
              fontSize: 12, marginBottom: 12,
              color: message.type === "success" ? "var(--sage)" : "var(--rose)",
            }}>
              {message.text}
            </p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={submitting}
            className="btn-primary"
            style={{ width: "100%", height: 44, fontSize: 14 }}
          >
            {submitting ? "Saving..." : "Save Changes"}
          </button>
        </form>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}
