import { useState } from "react";

export default function Sidebar({
  dark,
  toggleTheme,
  resetWorkspace,
  appName,
  backendMode,
  user,
  onOpenAuth,
  onLogout,
  plan,
  usageToday,
  limit,
}) {
  const [accountOpen, setAccountOpen] = useState(false);

  const initial = user?.email ? user.email.charAt(0).toUpperCase() : null;

  return (
    <aside className="relative flex w-80 flex-col border-r border-gray-200 bg-white dark:border-gray-800 dark:bg-[#111111]">

      <div className="flex items-center justify-between border-b border-gray-100 px-6 py-6 dark:border-gray-800">
        <div className="text-lg font-semibold tracking-tight">
          {appName ?? "ReadPulse"}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={toggleTheme}
            className="rounded-md bg-gray-200 px-3 py-1 text-xs transition hover:opacity-80 dark:bg-gray-800"
          >
            {dark ? "Light" : "Dark"}
          </button>

          {user ? (
            <div className="relative">
              <button
                type="button"
                onClick={() => setAccountOpen((open) => !open)}
                className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-black to-gray-700 text-xs font-medium text-white shadow-sm dark:from-white dark:to-gray-300 dark:text-black"
              >
                {initial}
              </button>

              {accountOpen && (
                <div className="absolute right-0 top-10 w-64 rounded-2xl border border-gray-200 bg-white p-3 text-xs shadow-xl dark:border-gray-800 dark:bg-[#050505]">
                  <div className="mb-2 flex items-center gap-2">
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gray-900 text-[11px] font-medium text-white dark:bg-white dark:text-black">
                      {initial}
                    </div>
                    <div className="min-w-0">
                      <p className="truncate font-medium">
                        {user.email}
                      </p>
                      <p className="text-[10px] text-gray-400">
                        Account · ReadPulse
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={onLogout}
                    className="mt-1 w-full rounded-full bg-gray-900 px-3 py-1.5 text-[11px] font-medium text-white transition hover:opacity-90 dark:bg-white dark:text-black"
                  >
                    Log out
                  </button>

                  <p className="mt-2 text-[10px] text-gray-400">
                    Sessions sync to this browser. Perfect for testing before multi-device support.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <button
              type="button"
              onClick={() => onOpenAuth("signup")}
              className="rounded-full border border-gray-200 px-3 py-1 text-xs font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-100 dark:hover:bg-gray-900"
            >
              Sign up / Log in
            </button>
          )}
        </div>
      </div>

      <div className="px-6 py-6">
        <button
          onClick={resetWorkspace}
          className="w-full px-6 py-2.5 rounded-full text-sm font-medium bg-black text-white dark:bg-white dark:text-black hover:opacity-90 transition"
        >
          + New Summary
        </button>
      </div>

      <div className="mt-auto border-t border-gray-100 px-6 py-3 text-xs text-gray-400 dark:border-gray-800">
        {backendMode && (
          <p className="mb-1">
            Backend: {backendMode}
          </p>
        )}
        {limit != null && (
          <p>
            Plan: <span className="font-medium capitalize">{plan || "free"}</span>{" "}
            · Today: {usageToday ?? 0}/{limit}
          </p>
        )}
      </div>

    </aside>
  );
}