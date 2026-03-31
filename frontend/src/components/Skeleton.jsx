/**
 * Skeleton — Shimmer loading placeholders for better perceived performance.
 *
 * Task #41: Replace "Loading…" text with animated skeleton screens.
 * Uses CSS custom properties from the design system.
 */
import { memo } from "react";

const shimmerStyle = {
  background: `linear-gradient(
    90deg,
    var(--bg-surface) 0%,
    var(--bg-raised, rgba(255,255,255,0.06)) 40%,
    var(--bg-surface) 80%
  )`,
  backgroundSize: "200% 100%",
  animation: "skeleton-shimmer 1.5s ease-in-out infinite",
  borderRadius: 8,
};

/**
 * Base skeleton block — rectangular shimmer placeholder.
 */
export const SkeletonBlock = memo(function SkeletonBlock({
  width = "100%",
  height = 16,
  borderRadius = 8,
  style = {},
}) {
  return (
    <div
      style={{
        ...shimmerStyle,
        width,
        height,
        borderRadius,
        ...style,
      }}
    />
  );
});

/**
 * Skeleton text line — a single line of "text."
 */
export const SkeletonLine = memo(function SkeletonLine({
  width = "100%",
  height = 14,
  style = {},
}) {
  return <SkeletonBlock width={width} height={height} borderRadius={4} style={style} />;
});

/**
 * SkeletonCard — Full card placeholder (title + lines + action bar).
 */
export const SkeletonCard = memo(function SkeletonCard({ lines = 3 }) {
  return (
    <div
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border-dim)",
        borderRadius: 12,
        padding: 24,
        marginBottom: 16,
      }}
    >
      {/* Title */}
      <SkeletonBlock width="60%" height={20} style={{ marginBottom: 16 }} />

      {/* Body lines */}
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonLine
          key={i}
          width={i === lines - 1 ? "40%" : "100%"}
          style={{ marginBottom: 10 }}
        />
      ))}

      {/* Action bar */}
      <div style={{ display: "flex", gap: 12, marginTop: 20 }}>
        <SkeletonBlock width={80} height={32} borderRadius={6} />
        <SkeletonBlock width={100} height={32} borderRadius={6} />
      </div>
    </div>
  );
});

/**
 * SkeletonDashboard — Analytics dashboard placeholder.
 */
export const SkeletonDashboard = memo(function SkeletonDashboard() {
  return (
    <div>
      {/* Stats row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginBottom: 32 }}>
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border-dim)",
              borderRadius: 12,
              padding: 20,
            }}
          >
            <SkeletonLine width="50%" height={12} style={{ marginBottom: 12 }} />
            <SkeletonBlock width="70%" height={28} />
          </div>
        ))}
      </div>

      {/* Chart area */}
      <SkeletonBlock width="100%" height={240} style={{ marginBottom: 24 }} />

      {/* Table rows */}
      {[1, 2, 3].map((i) => (
        <SkeletonLine key={i} width="100%" height={44} style={{ marginBottom: 8 }} />
      ))}
    </div>
  );
});

/**
 * SkeletonSummarizer — Summarizer output placeholder.
 */
export const SkeletonSummarizer = memo(function SkeletonSummarizer() {
  return (
    <div
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border-dim)",
        borderRadius: 12,
        padding: 24,
      }}
    >
      <SkeletonBlock width="40%" height={18} style={{ marginBottom: 20 }} />
      <SkeletonLine width="100%" style={{ marginBottom: 10 }} />
      <SkeletonLine width="95%" style={{ marginBottom: 10 }} />
      <SkeletonLine width="100%" style={{ marginBottom: 10 }} />
      <SkeletonLine width="88%" style={{ marginBottom: 10 }} />
      <SkeletonLine width="60%" style={{ marginBottom: 20 }} />

      {/* Takeaways */}
      <SkeletonBlock width="30%" height={16} style={{ marginBottom: 14 }} />
      {[1, 2, 3].map((i) => (
        <div key={i} style={{ display: "flex", gap: 8, marginBottom: 8, alignItems: "center" }}>
          <SkeletonBlock width={6} height={6} borderRadius={3} />
          <SkeletonLine width={`${70 + i * 5}%`} />
        </div>
      ))}
    </div>
  );
});
