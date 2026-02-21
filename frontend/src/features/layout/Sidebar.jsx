export default function Sidebar({ dark, toggleTheme, resetWorkspace }) {
  return (
    <aside className="w-80 bg-white dark:bg-[#111111] border-r border-gray-200 dark:border-gray-800 flex flex-col">

      <div className="px-6 py-6 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center">
        <div className="text-lg font-semibold tracking-tight">
          ReadPulse
        </div>

        <button
          onClick={toggleTheme}
          className="text-xs px-3 py-1 rounded-md bg-gray-200 dark:bg-gray-800 hover:opacity-80 transition"
        >
          {dark ? "Light" : "Dark"}
        </button>
      </div>

      <div className="px-6 py-6">
        <button
          onClick={resetWorkspace}
          className="w-full px-6 py-2.5 rounded-full text-sm font-medium bg-black text-white dark:bg-white dark:text-black hover:opacity-90 transition"
        >
          + New Summary
        </button>
      </div>

    </aside>
  );
}