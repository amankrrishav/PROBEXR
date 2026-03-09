/**
 * SummaryStats — Animated stat badges for the summarizer output.
 * Uses the design system CSS variables.
 */
export default function SummaryStats({ meta }) {
  if (!meta) return null;

  // Most stats are shown inline via chips in OutputCard now,
  // so this component is kept lightweight for additional detail
  const readability = meta.readability_grade;
  const contentType = meta.content_type;

  if (!readability && !contentType) return null;

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {contentType && (
        <span className="chip" style={{ textTransform: "capitalize" }}>
          {contentType}
        </span>
      )}
      {readability && (
        <span className="chip">
          Grade {readability}
        </span>
      )}
    </div>
  );
}
