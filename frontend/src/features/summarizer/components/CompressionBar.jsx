/**
 * CompressionBar — Visual bar showing input vs output word-count ratio.
 */
import { useState, useEffect, useRef } from "react";

/* ── Animated Counter ── */
function useAnimatedValue(target, duration = 800) {
  const [value, setValue] = useState(0);
  const raf = useRef(null);
  useEffect(() => {
    if (!target) { 
        requestAnimationFrame(() => setValue(0)); 
        return; 
    }
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

/* ── Compression Bar ── */
export default function CompressionBar({ originalWords, summaryWords }) {
  const [animReady, setAnimReady] = useState(false);
  const animOriginal = useAnimatedValue(animReady ? (originalWords || 0) : 0);
  const animSummary = useAnimatedValue(animReady ? (summaryWords || 0) : 0);

  useEffect(() => {
    const t = setTimeout(() => setAnimReady(true), 100);
    return () => clearTimeout(t);
  }, []);

  if (!originalWords || !summaryWords) return null;
  const ratio = Math.round((summaryWords / originalWords) * 100);

  return (
    <div style={{ marginTop: 16 }}>
      <p className="section-header" style={{ marginBottom: 12 }}>Compression</p>
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-3">
          <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-tertiary)", width: 56, textAlign: "right" }}>
            Original
          </span>
          <div className="compression-bar" style={{ flex: 1 }}>
            <div className="fill" style={{
              width: animReady ? "100%" : "0%",
              background: "var(--border-lit)",
            }} />
          </div>
          <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-secondary)", width: 56 }}>
            {animOriginal.toLocaleString()}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-tertiary)", width: 56, textAlign: "right" }}>
            Summary
          </span>
          <div className="compression-bar" style={{ flex: 1 }}>
            <div className="fill" style={{
              width: animReady ? `${ratio}%` : "0%",
              background: "var(--amber)",
              boxShadow: "var(--glow-amber)",
            }} />
          </div>
          <span className="font-mono" style={{ fontSize: 11, color: "var(--amber)", width: 56 }}>
            {animSummary.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
}
