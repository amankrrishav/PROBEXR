/**
 * KeyThemesGraph — SVG node graph showing key themes from the summary.
 * Renders 6-8 themes as connected amber circles.
 */
import { useState, useMemo } from "react";

export default function KeyThemesGraph({ themes, onThemeClick }) {
  const [hoveredNode, setHoveredNode] = useState(null);
  const [collapsed, setCollapsed] = useState(false);

  if (!themes || themes.length === 0) return null;

  // Layout nodes in a circle/ellipse pattern
  const nodeData = useMemo(() => {
    const cx = 250, cy = 120;
    const rx = 180, ry = 70;
    return themes.slice(0, 8).map((theme, i) => {
      const angle = (i / Math.min(themes.length, 8)) * 2 * Math.PI - Math.PI / 2;
      return {
        id: i,
        label: typeof theme === "string" ? theme : theme.text || theme.label || `Theme ${i+1}`,
        x: cx + rx * Math.cos(angle),
        y: cy + ry * Math.sin(angle),
        size: 6 + (themes.length - i) * 1.5, // larger = more important
      };
    });
  }, [themes]);

  // Create edges between adjacent themes (simple heuristic)
  const edges = useMemo(() => {
    const result = [];
    for (let i = 0; i < nodeData.length; i++) {
      const next = (i + 1) % nodeData.length;
      result.push({ from: nodeData[i], to: nodeData[next] });
      // Also connect nodes that are 2 apart for denser graph
      if (nodeData.length > 3) {
        const skip = (i + 2) % nodeData.length;
        result.push({ from: nodeData[i], to: nodeData[skip] });
      }
    }
    return result;
  }, [nodeData]);

  return (
    <div style={{ marginTop: 16 }}>
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center gap-2 w-full"
        style={{
          background: "none", border: "none", cursor: "pointer",
          padding: "8px 0", color: "var(--ink-tertiary)",
        }}
      >
        <span className="section-header" style={{ padding: 0, margin: 0 }}>Key Themes</span>
        <span style={{ flex: 1, height: 1, background: "var(--border-dim)" }} />
        <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-tertiary)" }}>
          {collapsed ? "Show" : "Hide"}
        </span>
      </button>

      {!collapsed && (
        <div className="animate-in" style={{
          background: "var(--bg-elevated)",
          borderRadius: "var(--radius-card)",
          padding: "20px",
          marginTop: 8,
        }}>
          <svg width="100%" viewBox="0 0 500 240" style={{ overflow: "visible" }}>
            {/* Edges */}
            {edges.map((e, i) => (
              <line
                key={i}
                className="theme-edge"
                x1={e.from.x} y1={e.from.y}
                x2={e.to.x} y2={e.to.y}
                style={{
                  opacity: hoveredNode !== null
                    ? (hoveredNode === e.from.id || hoveredNode === e.to.id ? 0.6 : 0.15)
                    : 0.3,
                }}
              />
            ))}

            {/* Nodes */}
            {nodeData.map((node) => (
              <g key={node.id}>
                <circle
                  cx={node.x} cy={node.y} r={node.size}
                  fill="var(--amber)"
                  opacity={hoveredNode === node.id ? 1 : 0.7}
                  className="theme-node"
                  style={{
                    filter: hoveredNode === node.id ? "drop-shadow(0 0 8px rgba(232,150,12,0.5))" : "none",
                  }}
                  onMouseEnter={() => setHoveredNode(node.id)}
                  onMouseLeave={() => setHoveredNode(null)}
                  onClick={() => onThemeClick?.(node.label)}
                />
                <text
                  className="theme-node-label"
                  x={node.x} y={node.y + node.size + 14}
                  style={{
                    opacity: hoveredNode === null || hoveredNode === node.id ? 1 : 0.4,
                  }}
                >
                  {node.label.length > 16 ? node.label.slice(0, 16) + "…" : node.label}
                </text>
              </g>
            ))}
          </svg>
        </div>
      )}
    </div>
  );
}
