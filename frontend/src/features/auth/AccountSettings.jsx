import { useState } from "react";
import { useAppContext } from "../../contexts/AppContext";
import { config } from "../../config";

export default function AccountSettings({ open, onClose }) {
  const { auth } = useAppContext();
  const { user } = auth;
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || "");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState(null);

  if (!open) return null;

  async function handleUpdate(e) {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      await auth.updateProfile({
        full_name: fullName.trim() || null,
        avatar_url: avatarUrl.trim() || null,
      });

      setMessage({ type: "success", text: "Profile updated successfully!" });
      setTimeout(onClose, 1500);
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="relative w-full max-w-md rounded-2xl bg-white/95 p-6 shadow-2xl dark:bg-[#111111]/95 border border-gray-200 dark:border-gray-800">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
        >
          Esc
        </button>

        <h2 className="text-lg font-semibold tracking-tight mb-4">Account Settings</h2>

        <form onSubmit={handleUpdate} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-gray-300">
              Full Name
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm outline-none ring-0 transition focus:border-black focus:ring-1 focus:ring-black dark:border-gray-700 dark:bg-[#050505] dark:focus:border-white dark:focus:ring-white"
              placeholder="e.g. Jane Doe"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-gray-300">
              Avatar URL
            </label>
            <input
              type="text"
              value={avatarUrl}
              onChange={(e) => setAvatarUrl(e.target.value)}
              className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm outline-none ring-0 transition focus:border-black focus:ring-1 focus:ring-black dark:border-gray-700 dark:bg-[#050505] dark:focus:border-white dark:focus:ring-white"
              placeholder="https://..."
            />
            <p className="text-[10px] text-gray-400">External images only for now.</p>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-gray-300">
              Email
            </label>
            <input
              type="email"
              disabled
              value={user?.email || ""}
              className="w-full rounded-xl border border-gray-100 bg-gray-50 px-3 py-2 text-sm text-gray-400 dark:border-gray-800 dark:bg-[#0a0a0a]"
            />
            <p className="text-[10px] text-gray-400">Email changes coming soon.</p>
          </div>

          {message && (
            <p className={`text-[11px] ${message.type === "success" ? "text-emerald-500" : "text-red-500"}`}>
              {message.text}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-full bg-black px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:opacity-90 disabled:opacity-70 dark:bg-white dark:text-black"
          >
            {submitting ? "Updating..." : "Save Changes"}
          </button>
        </form>
      </div>
    </div>
  );
}
