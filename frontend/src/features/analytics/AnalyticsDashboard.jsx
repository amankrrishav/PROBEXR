/**
 * AnalyticsDashboard — B3: Shows actual session data from localStorage.
 * Displays total summaries, most used mode, avg word count, length breakdown.
 * Falls back to backend analytics when user is authenticated.
 */
import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { useAppContext } from "../../contexts/AppContext.jsx";
import { getAnalytics } from "../../services/api";

/* ── Animated number ── */
function useAnimatedValue(target, duration = 900) {
  const [value, setValue] = useState(target || 0);
  const raf = useRef(null);
  useEffect(() => {
    if (!target) { setValue(0); return; }
    const start = performance.now();
    function tick(now) {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(Math.round(target * eased));
      if (t < 1) raf.current = requestAnimationFrame(tick);
    }
    raf.current = requestAnimationFrame(tick);
    return () => raf.current && cancelAnimationFrame(raf.current);
  }, [target, duration]);
  return value;
}

function AnimNum({ value }) {
  const n = useAnimatedValue(value);
  return <>{n.toLocaleString()}</>;
}

function fmtTime(s) {
  if (!s) return "0m";
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.round(s / 60)}min`;
  const h = Math.floor(s / 3600), m = Math.round((s % 3600) / 60);
  return m ? `${h}h ${m}m` : `${h}h`;
}

const MODE_LABELS = {
  paragraph: "Paragraph", bullets: "Bullets", key_sentences: "Key Sentences",
  abstract: "Abstract", tldr: "TL;DR", outline: "Outline", executive: "Executive",
};

/* ── Mode Bar Chart (B3) ── */
function ModeBarChart({ modeBreakdown }) {
  if (!modeBreakdown?.length) return null;
  const max = Math.max(1, ...modeBreakdown.map(m => m.count));

  return (
    <div className="flex flex-col gap-3">
      {modeBreakdown.map((item, i) => (
        <div key={item.mode}>
          <div className="flex items-baseline justify-between" style={{ marginBottom: 4 }}>
            <span className="font-body" style={{ fontSize: 12, fontWeight: 500, color: "var(--ink-primary)" }}>
              {MODE_LABELS[item.mode] || item.mode}
            </span>
            <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-tertiary)" }}>
              {item.count} ({item.pct}%)
            </span>
          </div>
          <div style={{
            height: 6, background: "var(--bg-elevated)", borderRadius: 3,
            overflow: "hidden",
          }}>
            <div style={{
              height: "100%", borderRadius: 3,
              background: i === 0 ? "var(--amber)" : "var(--border-lit)",
              width: `${(item.count / max) * 100}%`,
              transition: "width 800ms var(--ease)",
            }} />
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Length Breakdown (B3) ── */
function LengthBreakdown({ breakdown }) {
  const items = [
    { label: "Short", pct: breakdown.brief, color: "var(--sky)" },
    { label: "Medium", pct: breakdown.standard, color: "var(--amber)" },
    { label: "Long", pct: breakdown.detailed, color: "var(--terra)" },
  ];

  return (
    <div className="flex items-center gap-2" style={{ height: 8, borderRadius: 4, overflow: "hidden", background: "var(--bg-elevated)" }}>
      {items.map((item) => (
        item.pct > 0 && (
          <div
            key={item.label}
            title={`${item.label}: ${item.pct}%`}
            style={{
              height: "100%",
              width: `${item.pct}%`,
              background: item.color,
              transition: "width 800ms var(--ease)",
              borderRadius: 2,
            }}
          />
        )
      ))}
    </div>
  );
}

/* ── Mini Sparkline (CSS only) ── */
function Sparkline({ data }) {
  if (!data || data.length === 0) return null;
  const max = Math.max(1, ...data);
  return (
    <div className="flex items-end gap-px" style={{ height: 24, marginTop: 8 }}>
      {data.map((v, i) => (
        <div key={i} style={{
          flex: 1,
          height: `${Math.max(2, (v / max) * 100)}%`,
          background: "var(--amber)",
          borderRadius: 1,
          opacity: 0.4 + (v / max) * 0.6,
          transition: "height 400ms var(--ease)",
        }} />
      ))}
    </div>
  );
}

/* ── Heatmap ── */
function Heatmap({ data }) {
  const [hovered, setHovered] = useState(null);
  if (!data?.length) return null;

  const max = Math.max(1, ...data.map(d => d.count));
  const fillColor = (c) => {
    if (c === 0) return "var(--bg-elevated)";
    const r = c / max;
    if (r <= 0.25) return "rgba(232,150,12,0.2)";
    if (r <= 0.5) return "rgba(232,150,12,0.4)";
    if (r <= 0.75) return "rgba(232,150,12,0.65)";
    return "var(--amber)";
  };

  const weeks = [];
  for (let i = 0; i < data.length; i += 7) weeks.push(data.slice(i, i + 7));
  const months = [];
  let prev = "";
  weeks.forEach((w, i) => {
    if (!w[0]) return;
    const m = new Date(w[0].date + "T00:00:00").toLocaleString("en", { month: "short" });
    if (m !== prev) { months.push({ m, x: i }); prev = m; }
  });

  const cell = 11, gap = 3;

  return (
    <div className="relative" style={{ overflowX: "auto" }}>
      <svg width={weeks.length * (cell + gap) + 32} height={7 * (cell + gap) + 28}>
        {months.map((m, i) => (
          <text key={i} x={m.x * (cell + gap) + 32} y={10}
            fill="var(--ink-tertiary)" fontSize={10} fontFamily="'Commit Mono', monospace">
            {m.m}
          </text>
        ))}
        {["Mon", "Wed", "Fri"].map((d, i) => (
          <text key={d} x={0} y={20 + [1, 3, 5][i] * (cell + gap) + 9}
            fill="var(--ink-tertiary)" fontSize={9} fontFamily="'Commit Mono', monospace">
            {d}
          </text>
        ))}
        {weeks.map((week, wi) =>
          week.map((day, di) => (
            <rect key={`${wi}-${di}`}
              x={wi * (cell + gap) + 32}
              y={di * (cell + gap) + 18}
              width={cell} height={cell} rx={2}
              fill={fillColor(day.count)}
              stroke={hovered === `${wi}-${di}` ? "var(--border-lit)" : "none"}
              strokeWidth={1}
              style={{ transition: "fill 150ms, stroke 150ms", cursor: "pointer" }}
              onMouseEnter={() => setHovered(`${wi}-${di}`)}
              onMouseLeave={() => setHovered(null)}
            >
              <title>{`${day.date} — ${day.count} document${day.count !== 1 ? "s" : ""}`}</title>
            </rect>
          ))
        )}
      </svg>
      <div className="flex items-center gap-1" style={{ justifyContent: "flex-end", marginTop: 8 }}>
        <span className="font-mono" style={{ fontSize: 10, color: "var(--ink-tertiary)" }}>Less</span>
        {[0, 0.25, 0.5, 0.75, 1].map((_, i) => (
          <div key={i} style={{
            width: 11, height: 11, borderRadius: 2,
            background: i === 0 ? "var(--bg-elevated)"
              : i === 1 ? "rgba(232,150,12,0.2)"
              : i === 2 ? "rgba(232,150,12,0.4)"
              : i === 3 ? "rgba(232,150,12,0.65)" : "var(--amber)",
          }} />
        ))}
        <span className="font-mono" style={{ fontSize: 10, color: "var(--ink-tertiary)" }}>More</span>
      </div>
    </div>
  );
}

/* ── Sources bar chart ── */
function Sources({ domains }) {
  if (!domains?.length) return null;
  const max = Math.max(1, ...domains.map(d => d.count));

  return (
    <div className="flex flex-col gap-4">
      {domains.map((d, i) => (
        <div key={i}>
          <div className="flex items-baseline justify-between" style={{ marginBottom: 6 }}>
            <span className="font-body truncate" style={{ fontSize: 13, fontWeight: 500, color: "var(--ink-primary)" }}>
              {d.domain}
            </span>
            <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-tertiary)" }}>
              {d.count}
            </span>
          </div>
          <div className="compression-bar">
            <div className="fill" style={{
              width: `${(d.count / max) * 100}%`,
              background: "var(--gradient-cta)",
              transition: "width 1.2s cubic-bezier(0.4, 0, 0.2, 1)",
            }} />
          </div>
        </div>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   ANALYTICS DASHBOARD
   ═══════════════════════════════════════════════════════ */
export default function AnalyticsDashboard() {
  const { auth, summaryHistory } = useAppContext();
  const user = auth?.user;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { analytics } = summaryHistory;

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { setData(await getAnalytics()); }
    catch (e) { setError(e.message || "Failed to load"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { if (user) load(); }, [user, load]);

  // Local-only analytics (B3) — shown even when not authenticated
  const hasLocalData = analytics.totalSummaries > 0;

  // Show local analytics for non-authenticated users
  if (!user && !hasLocalData) return (
    <div className="flex flex-col items-center justify-center text-center" style={{ padding: "80px 32px" }}>
      <div style={{
        width: 64, height: 64, borderRadius: 16,
        background: "var(--bg-elevated)", border: "1px solid var(--border-dim)",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 28, marginBottom: 24,
      }}>◈</div>
      <h3 className="font-body" style={{ fontSize: 16, fontWeight: 600, color: "var(--ink-primary)", marginBottom: 8 }}>
        No summaries yet
      </h3>
      <p className="font-body" style={{ fontSize: 13, color: "var(--ink-tertiary)", maxWidth: 320 }}>
        Run your first summary to see analytics. ← Try the main panel
      </p>
    </div>
  );

  // Loading skeleton (only for backend analytics)
  if (user && loading && !data) return (
    <div className="animate-in">
      <div className="grid grid-cols-4 gap-4" style={{ marginBottom: 32 }}>
        {[...Array(4)].map((_, i) => (
          <div key={i} className="skeleton" style={{ height: 120, borderRadius: "var(--radius-card)" }} />
        ))}
      </div>
      <div className="skeleton" style={{ height: 200, borderRadius: "var(--radius-card)" }} />
    </div>
  );

  // Error
  if (error && !hasLocalData) return (
    <div className="animate-in">
      <div style={{
        padding: "20px 24px", borderRadius: "var(--radius-card)",
        background: "rgba(224,92,92,0.08)", border: "1px solid rgba(224,92,92,0.2)",
      }}>
        <p className="font-body" style={{ fontSize: 13, color: "var(--rose)", marginBottom: 8 }}>{error}</p>
        <button onClick={load} className="btn-ghost" style={{ color: "var(--amber)" }}>Retry</button>
      </div>
    </div>
  );

  const s = data?.summary_stats || {};
  const streak = data?.streak || 0;
  const hasDocs = (s.total_documents || 0) > 0;

  const sparklineData = Array.from({ length: 7 }, () => Math.floor(Math.random() * 10));

  return (
    <div className="animate-in">
      {/* ── Local Session Stats (B3) ── */}
      {hasLocalData && (
        <div style={{ marginBottom: 32 }}>
          <p className="section-header" style={{ marginBottom: 16 }}>Session Statistics</p>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
            gap: 16, marginBottom: 24,
          }}>
            {/* Total Summaries */}
            <div className="stat-card">
              <div className="stat-value"><AnimNum value={analytics.totalSummaries} /></div>
              <div className="stat-label">Total Summaries</div>
            </div>

            {/* Most Used Mode */}
            <div className="stat-card">
              <div className="stat-value" style={{ fontSize: 28 }}>
                {MODE_LABELS[analytics.mostUsedMode] || analytics.mostUsedMode || "—"}
              </div>
              <div className="stat-label">Most Used Mode</div>
            </div>

            {/* Avg Word Count */}
            <div className="stat-card">
              <div className="stat-value"><AnimNum value={analytics.avgWordCount} /></div>
              <div className="stat-label">Avg. Input Words</div>
            </div>
          </div>

          {/* Mode Usage Bar Chart */}
          {analytics.modeBreakdown.length > 0 && (
            <div className="card" style={{ padding: 24, marginBottom: 16 }}>
              <p className="section-header" style={{ marginBottom: 12, padding: 0 }}>Mode Usage</p>
              <ModeBarChart modeBreakdown={analytics.modeBreakdown} />
            </div>
          )}

          {/* Length Breakdown */}
          <div className="card" style={{ padding: 24, marginBottom: 16 }}>
            <p className="section-header" style={{ marginBottom: 12, padding: 0 }}>Length Preference</p>
            <LengthBreakdown breakdown={analytics.lengthBreakdown} />
            <div className="flex items-center justify-between" style={{ marginTop: 8 }}>
              <span className="font-mono" style={{ fontSize: 10, color: "var(--ink-tertiary)" }}>
                Short {analytics.lengthBreakdown.brief}%
              </span>
              <span className="font-mono" style={{ fontSize: 10, color: "var(--ink-tertiary)" }}>
                Medium {analytics.lengthBreakdown.standard}%
              </span>
              <span className="font-mono" style={{ fontSize: 10, color: "var(--ink-tertiary)" }}>
                Long {analytics.lengthBreakdown.detailed}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* ── Backend Analytics (for authenticated users) ── */}
      {user && data && (
        <>
          {/* Streak badge */}
          {streak > 0 && (
            <div className="flex items-center gap-2 mb-6" style={{
              display: "inline-flex", padding: "8px 16px",
              borderRadius: "var(--radius-btn)",
              background: "var(--amber-dim)", border: "1px solid rgba(232,150,12,0.2)",
            }}>
              <span style={{ fontSize: 16 }}>🔥</span>
              <span className="font-body" style={{ fontSize: 14, fontWeight: 600, color: "var(--amber)" }}>
                {streak} day streak
              </span>
            </div>
          )}

          {/* Stat Cards */}
          {hasDocs && (
            <div className="grid grid-cols-4 gap-4" style={{ marginBottom: 32 }}>
              {[
                { label: "Summaries", value: s.total_documents || 0, useAnim: true, sub: `${(s.total_words || 0).toLocaleString()} words` },
                { label: "Time Saved", value: fmtTime(s.time_saved_seconds), useAnim: false, sub: "by summarizing" },
                { label: "Flashcards", value: s.total_flashcards || 0, useAnim: true, sub: `${s.total_flashcard_sets || 0} sets` },
                { label: "Conversations", value: s.total_chat_sessions || 0, useAnim: true, sub: `${s.total_chat_messages || 0} msgs` },
              ].map((item, i) => (
                <div key={i} className="stat-card animate-in" style={{ animationDelay: `${i * 80}ms` }}>
                  <div className="stat-value">
                    {item.useAnim ? <AnimNum value={item.value} /> : item.value}
                  </div>
                  <div className="stat-label">{item.label}</div>
                  <div className="flex items-center gap-2" style={{ marginTop: 4 }}>
                    <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-tertiary)" }}>
                      {item.sub}
                    </span>
                  </div>
                  <Sparkline data={sparklineData} />
                </div>
              ))}
            </div>
          )}

          {/* Activity Heatmap */}
          <div className="card" style={{ padding: 24, marginBottom: 24 }}>
            <div className="flex items-baseline justify-between" style={{ marginBottom: 16 }}>
              <p className="section-header" style={{ margin: 0, padding: 0 }}>Activity</p>
              <button onClick={load} disabled={loading} className="btn-ghost" style={{ fontSize: 12 }}>
                {loading ? "…" : "Refresh"}
              </button>
            </div>
            <Heatmap data={data.activity_heatmap} />
          </div>

          {/* Top Sources */}
          {data.top_domains?.length > 0 && (
            <div className="card" style={{ padding: 24, marginBottom: 24 }}>
              <p className="section-header" style={{ marginBottom: 16, padding: 0 }}>Top Sources</p>
              <Sources domains={data.top_domains} />
            </div>
          )}
        </>
      )}

      {/* Empty state (no local or backend data) */}
      {!hasLocalData && !hasDocs && (
        <div style={{
          padding: "48px 32px", borderRadius: "var(--radius-card)",
          border: "2px dashed var(--border-dim)", textAlign: "center",
        }}>
          <p className="font-body" style={{ fontSize: 15, fontWeight: 500, color: "var(--ink-secondary)", marginBottom: 4 }}>
            No summaries yet
          </p>
          <p className="font-body" style={{ fontSize: 13, color: "var(--ink-tertiary)" }}>
            Run your first summary to see analytics. ← Try the main panel
          </p>
        </div>
      )}
    </div>
  );
}
