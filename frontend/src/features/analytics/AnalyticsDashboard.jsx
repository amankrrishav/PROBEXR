import { useState, useEffect, useCallback, useRef } from "react";
import { useAppContext } from "../../contexts/AppContext.jsx";
import { getAnalytics } from "../../services/api";

// ─── Animated number ─────────────────────────────────────────────────
function useAnimatedValue(target, duration = 900) {
    const [value, setValue] = useState(target || 0);
    const raf = useRef(null);

    useEffect(() => {
        if (!target) {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setValue(0);
            return;
        }
        const start = performance.now();
        const from = 0;
        function tick(now) {
            const t = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - t, 3); // ease-out cubic
            setValue(Math.round(from + (target - from) * eased));
            if (t < 1) raf.current = requestAnimationFrame(tick);
        }
        raf.current = requestAnimationFrame(tick);
        return () => raf.current && cancelAnimationFrame(raf.current);
    }, [target, duration]);
    return value;
}

function AnimNum({ value, suffix = "" }) {
    const n = useAnimatedValue(value);
    return <>{n.toLocaleString()}{suffix}</>;
}

// ─── Format helpers ──────────────────────────────────────────────────
function fmtTime(s) {
    if (!s) return "0m";
    if (s < 60) return `${s}s`;
    if (s < 3600) return `${Math.round(s / 60)}min`;
    const h = Math.floor(s / 3600), m = Math.round((s % 3600) / 60);
    return m ? `${h}h ${m}m` : `${h}h`;
}

// ─── Contribution Heatmap (GitHub-style) ─────────────────────────────
function Heatmap({ data }) {
    const [hoveredDay, setHoveredDay] = useState(null);
    if (!data?.length) return null;

    const max = Math.max(1, ...data.map(d => d.count));

    const fill = (c) => {
        if (c === 0) return "fill-[#ebedf0] dark:fill-[#161b22]";
        const r = c / max;
        if (r <= 0.25) return "fill-[#9be9a8] dark:fill-[#0e4429]";
        if (r <= 0.5) return "fill-[#40c463] dark:fill-[#006d32]";
        if (r <= 0.75) return "fill-[#30a14e] dark:fill-[#26a641]";
        return "fill-[#216e39] dark:fill-[#39d353]";
    };

    // Build weeks
    const weeks = [];
    for (let i = 0; i < data.length; i += 7) weeks.push(data.slice(i, i + 7));

    // Month labels
    const months = [];
    let prev = "";
    weeks.forEach((w, i) => {
        if (!w[0]) return;
        const m = new Date(w[0].date + "T00:00:00").toLocaleString("en", { month: "short" });
        if (m !== prev) { months.push({ m, x: i }); prev = m; }
    });

    const cellSize = 11, gap = 3;

    return (
        <div className="relative">
            <svg
                width={weeks.length * (cellSize + gap) + 32}
                height={7 * (cellSize + gap) + 28}
                className="overflow-visible"
            >
                {/* Month labels */}
                {months.map((m, i) => (
                    <text
                        key={i}
                        x={m.x * (cellSize + gap) + 32}
                        y={10}
                        className="fill-gray-400 dark:fill-gray-500"
                        fontSize={10}
                        fontFamily="system-ui, -apple-system, sans-serif"
                    >
                        {m.m}
                    </text>
                ))}
                {/* Day labels */}
                {["Mon", "Wed", "Fri"].map((d, i) => (
                    <text
                        key={d}
                        x={0}
                        y={20 + ([1, 3, 5][i]) * (cellSize + gap) + 9}
                        className="fill-gray-400 dark:fill-gray-500"
                        fontSize={9}
                        fontFamily="system-ui, -apple-system, sans-serif"
                    >
                        {d}
                    </text>
                ))}
                {/* Cells */}
                {weeks.map((week, wi) =>
                    week.map((day, di) => (
                        <rect
                            key={`${wi}-${di}`}
                            x={wi * (cellSize + gap) + 32}
                            y={di * (cellSize + gap) + 18}
                            width={cellSize}
                            height={cellSize}
                            rx={2}
                            className={`${fill(day.count)} transition-all duration-150 ${hoveredDay === `${wi}-${di}` ? "stroke-gray-400 dark:stroke-gray-500 stroke-1" : ""}`}
                            onMouseEnter={() => setHoveredDay(`${wi}-${di}`)}
                            onMouseLeave={() => setHoveredDay(null)}
                        >
                            <title>{`${day.date} — ${day.count} document${day.count !== 1 ? "s" : ""}`}</title>
                        </rect>
                    ))
                )}
            </svg>
            {/* Legend */}
            <div className="flex items-center gap-1.5 mt-2 justify-end pr-1">
                <span className="text-[10px] text-gray-400 dark:text-gray-500 mr-0.5">Less</span>
                {[0, 0.25, 0.5, 0.75, 1].map((r, i) => {
                    const cls = r === 0
                        ? "bg-[#ebedf0] dark:bg-[#161b22]"
                        : r <= 0.25 ? "bg-[#9be9a8] dark:bg-[#0e4429]"
                            : r <= 0.5 ? "bg-[#40c463] dark:bg-[#006d32]"
                                : r <= 0.75 ? "bg-[#30a14e] dark:bg-[#26a641]"
                                    : "bg-[#216e39] dark:bg-[#39d353]";
                    return <div key={i} className={`w-[11px] h-[11px] rounded-sm ${cls}`} />;
                })}
                <span className="text-[10px] text-gray-400 dark:text-gray-500 ml-0.5">More</span>
            </div>
        </div>
    );
}

// ─── Top Sources ─────────────────────────────────────────────────────
function Sources({ domains }) {
    if (!domains?.length) return null;
    const max = Math.max(1, ...domains.map(d => d.count));

    return (
        <div className="space-y-3.5">
            {domains.map((d, i) => (
                <div key={i} className="group">
                    <div className="flex items-baseline justify-between mb-1.5">
                        <span className="text-[13px] font-medium text-gray-700 dark:text-gray-300 truncate mr-3">
                            {d.domain}
                        </span>
                        <span className="text-[11px] tabular-nums text-gray-400 dark:text-gray-500 shrink-0">
                            {d.count}
                        </span>
                    </div>
                    <div className="h-[3px] rounded-full bg-gray-100 dark:bg-gray-800/80 overflow-hidden">
                        <div
                            className="h-full rounded-full transition-all duration-[1.2s] ease-out"
                            style={{
                                width: `${(d.count / max) * 100}%`,
                                background: `linear-gradient(90deg, #818cf8, #a78bfa)`,
                            }}
                        />
                    </div>
                </div>
            ))}
        </div>
    );
}

// ═════════════════════════════════════════════════════════════════════
// DASHBOARD
// ═════════════════════════════════════════════════════════════════════
export default function AnalyticsDashboard() {
    const { auth } = useAppContext();
    const user = auth?.user;
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [entered, setEntered] = useState(false);

    const load = useCallback(async () => {
        setLoading(true); setError(null);
        try { setData(await getAnalytics()); }
        catch (e) { setError(e.message || "Failed to load"); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { if (user) load(); }, [user, load]);
    useEffect(() => { if (data) { const t = setTimeout(() => setEntered(true), 60); return () => clearTimeout(t); } }, [data]);

    /* ── Auth gate ── */
    if (!user) return (
        <div className="max-w-2xl mx-auto pt-8">
            <h1 className="text-[28px] font-semibold tracking-tight mb-2">Analytics</h1>
            <p className="text-[15px] text-gray-500 dark:text-gray-400 mb-10">
                Track your reading habits and measure progress.
            </p>
            <div className="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-[#111] p-10 text-center">
                <p className="text-[15px] font-medium mb-1">Sign in to view analytics</p>
                <p className="text-sm text-gray-400">Your reading data will appear here.</p>
            </div>
        </div>
    );

    /* ── Loading skeleton ── */
    if (loading && !data) return (
        <div className="max-w-4xl mx-auto pt-8">
            <div className="h-7 w-28 rounded-md bg-gray-200 dark:bg-gray-800 mb-8 animate-pulse" />
            <div className="grid grid-cols-4 gap-5 mb-10">
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-20 rounded-xl bg-gray-100 dark:bg-gray-800/50 animate-pulse" />
                ))}
            </div>
            <div className="h-44 rounded-xl bg-gray-100 dark:bg-gray-800/50 animate-pulse" />
        </div>
    );

    /* ── Error ── */
    if (error) return (
        <div className="max-w-2xl mx-auto pt-8">
            <h1 className="text-[28px] font-semibold tracking-tight mb-6">Analytics</h1>
            <div className="rounded-xl border border-red-200 dark:border-red-900/40 bg-red-50 dark:bg-red-950/10 p-5">
                <p className="text-sm text-red-600 dark:text-red-400 mb-2">{error}</p>
                <button onClick={load} className="text-xs underline text-red-500">Retry</button>
            </div>
        </div>
    );

    if (!data) return null;

    const s = data.summary_stats || {};
    const streak = data.streak || 0;
    const hasDocs = (s.total_documents || 0) > 0;

    /* ── Main layout ── */
    return (
        <div className={`max-w-4xl mx-auto pt-4 pb-16 transition-all duration-700 ${entered ? "opacity-100" : "opacity-0 translate-y-3"}`}>

            {/* ── Header row ── */}
            <div className="flex items-start justify-between mb-10">
                <div>
                    <h1 className="text-[28px] font-semibold tracking-tight mb-1">Analytics</h1>
                    <p className="text-[14px] text-gray-400 dark:text-gray-500">
                        {hasDocs
                            ? `${s.total_documents} document${s.total_documents !== 1 ? "s" : ""} · ${s.total_words?.toLocaleString()} words processed`
                            : "Start reading to see your analytics"}
                    </p>
                </div>
                {streak > 0 && (
                    <div className="flex items-center gap-2.5 px-4 py-2 rounded-full bg-orange-50 dark:bg-orange-950/20 border border-orange-200/60 dark:border-orange-800/30">
                        <span className="text-lg leading-none">🔥</span>
                        <div className="leading-tight">
                            <span className="text-[15px] font-semibold text-orange-600 dark:text-orange-400">{streak}</span>
                            <span className="text-[11px] text-orange-500/70 dark:text-orange-400/60 ml-1">day streak</span>
                        </div>
                    </div>
                )}
            </div>

            {/* ── Stat pills ── */}
            {hasDocs && (
                <div className="grid grid-cols-4 gap-4 mb-10">
                    {[
                        { label: "Time Saved", val: fmtTime(s.time_saved_seconds), sub: "by summarizing" },
                        { label: "Flashcards", val: s.total_flashcards || 0, num: true, sub: `${s.total_flashcard_sets || 0} sets` },
                        { label: "Conversations", val: s.total_chat_sessions || 0, num: true, sub: `${s.total_chat_messages || 0} messages` },
                        { label: "Documents", val: s.total_documents || 0, num: true, sub: `${s.total_words?.toLocaleString() || 0} words` },
                    ].map((item, i) => (
                        <div
                            key={i}
                            className={`rounded-xl border border-gray-200/80 dark:border-gray-800/80 bg-white dark:bg-[#111] px-5 py-4 transition-all duration-500 ${entered ? "opacity-100 translate-y-0" : "opacity-0 translate-y-3"}`}
                            style={{ transitionDelay: `${i * 80 + 100}ms` }}
                        >
                            <div className="text-[22px] font-semibold tracking-tight leading-tight mb-0.5">
                                {item.num ? <AnimNum value={item.val} /> : item.val}
                            </div>
                            <div className="text-[12px] font-medium text-gray-500 dark:text-gray-400">{item.label}</div>
                            <div className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">{item.sub}</div>
                        </div>
                    ))}
                </div>
            )}

            {/* ── Activity graph ── */}
            <div className={`mb-10 transition-all duration-600 ${entered ? "opacity-100 translate-y-0" : "opacity-0 translate-y-3"}`} style={{ transitionDelay: "420ms" }}>
                <div className="flex items-baseline justify-between mb-4">
                    <h2 className="text-[13px] font-medium text-gray-500 dark:text-gray-400">
                        Activity
                    </h2>
                    <button
                        onClick={load}
                        disabled={loading}
                        className="text-[11px] text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
                    >
                        {loading ? "…" : "Refresh"}
                    </button>
                </div>
                <div className="rounded-xl border border-gray-200/80 dark:border-gray-800/80 bg-white dark:bg-[#111] px-5 py-4 overflow-x-auto">
                    <Heatmap data={data.activity_heatmap} />
                </div>
            </div>

            {/* ── Bottom row: Sources ── */}
            {data.top_domains?.length > 0 && (
                <div className={`transition-all duration-600 ${entered ? "opacity-100 translate-y-0" : "opacity-0 translate-y-3"}`} style={{ transitionDelay: "540ms" }}>
                    <h2 className="text-[13px] font-medium text-gray-500 dark:text-gray-400 mb-4">
                        Top Sources
                    </h2>
                    <div className="rounded-xl border border-gray-200/80 dark:border-gray-800/80 bg-white dark:bg-[#111] px-5 py-5">
                        <Sources domains={data.top_domains} />
                    </div>
                </div>
            )}

            {/* ── Empty state ── */}
            {!hasDocs && (
                <div className="mt-4 rounded-xl border border-dashed border-gray-300 dark:border-gray-700 px-8 py-10 text-center">
                    <p className="text-[15px] font-medium mb-1">No reading data yet</p>
                    <p className="text-[13px] text-gray-400 dark:text-gray-500">
                        Summarize an article or paste a URL to start tracking your progress.
                    </p>
                </div>
            )}
        </div>
    );
}
