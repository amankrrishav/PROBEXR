import { useMemo } from "react";

/**
 * ComplexityMeter - Calculates and displays text intelligence score.
 */

function getIntelligenceScore(text) {
  if (!text || text.trim().split(/\s+/).length < 50) return null;
  const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
  const words = text.trim().split(/\s+/);
  const avgWordLen = words.reduce((s, w) => s + w.length, 0) / words.length;
  const avgSentLen = words.length / Math.max(sentences.length, 1);

  if (avgWordLen > 6.5 || avgSentLen > 28) return { level: "academic", color: "var(--sky)", label: "Expert-level content", pos: 90 };
  if (avgWordLen > 5.5 || avgSentLen > 22) return { level: "complex", color: "var(--terra)", label: "Advanced readers", pos: 70 };
  if (avgWordLen > 4.5 || avgSentLen > 16) return { level: "moderate", color: "var(--amber)", label: "General audience", pos: 45 };
  return { level: "simple", color: "var(--sage)", label: "Readable by most", pos: 15 };
}

export default function ComplexityMeter({ text, hasSummary }) {
  const intelligenceScore = useMemo(() => getIntelligenceScore(text), [text]);

  if (hasSummary || !intelligenceScore) return null;

  return (
    <div style={{ padding: "0 24px" }}>
      <div className="intelligence-meter">
        <span className="font-mono" style={{ fontSize: 10, color: "var(--ink-tertiary)", textTransform: "uppercase", letterSpacing: "0.1em" }}>
          Text Complexity
        </span>
        <div className="track">
          <div className="indicator" style={{
            left: `${intelligenceScore.pos}%`,
            background: intelligenceScore.color,
            boxShadow: `0 0 8px ${intelligenceScore.color}`,
          }} />
        </div>
        <span className="intelligence-meter label" style={{ color: intelligenceScore.color, textAlign: "right" }}>
          {intelligenceScore.label}
        </span>
      </div>
    </div>
  );
}
