/**
 * KeyTakeaways — Styled takeaway list with warm amber markers.
 */
export default function KeyTakeaways({ takeaways }) {
  if (!takeaways || takeaways.length === 0) return null;

  return (
    <div>
      <p className="section-header" style={{ marginBottom: 12 }}>Key Takeaways</p>
      <div className="flex flex-col gap-2">
        {takeaways.map((t, i) => (
          <div
            key={i}
            className="flex items-start gap-3 animate-in"
            style={{ animationDelay: `${i * 80}ms` }}
          >
            <div style={{
              width: 20, height: 20, borderRadius: 6, marginTop: 2,
              background: "var(--amber-dim)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 10, fontWeight: 700, color: "var(--amber)",
              flexShrink: 0,
            }}>
              {i + 1}
            </div>
            <p className="font-body" style={{
              fontSize: 13, lineHeight: 1.6,
              color: "var(--ink-secondary)", margin: 0,
            }}>
              {t}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
