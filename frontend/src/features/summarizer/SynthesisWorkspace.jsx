import { useState, useMemo } from "react";
import { useAppContext } from "../../contexts/AppContext.jsx";
import { synthesizeDocuments } from "../../services/api";

const SYNTHESIS_MODES = [
  { value: "unified", label: "Unified Summary", icon: "⊞", desc: "Merges into one" },
  { value: "compare", label: "Compare & Contrast", icon: "⇔", desc: "Side-by-side analysis" },
  { value: "disagreements", label: "Find Disagreements", icon: "⚡", desc: "Contradictory claims" },
  { value: "timeline", label: "Timeline Merge", icon: "⟿", desc: "Chronological order" },
];

/* ── Document DNA Visualization ── */
function DocumentDNA({ docA, docB }) {
  const statsA = useMemo(() => computeDocStats(docA), [docA]);
  const statsB = useMemo(() => computeDocStats(docB), [docB]);

  const overlap = useMemo(() => {
    if (!docA.trim() || !docB.trim()) return 0;
    const wordsA = new Set(docA.toLowerCase().match(/\b\w{3,}\b/g) || []);
    const wordsB = new Set(docB.toLowerCase().match(/\b\w{3,}\b/g) || []);
    const intersection = [...wordsA].filter(w => wordsB.has(w));
    const union = new Set([...wordsA, ...wordsB]);
    return union.size > 0 ? Math.round((intersection.length / union.size) * 100) : 0;
  }, [docA, docB]);

  if (!docA.trim() && !docB.trim()) return null;

  return (
    <div className="card" style={{ padding: 20, marginBottom: 16 }}>
      <p className="section-header" style={{ marginBottom: 12 }}>Document DNA</p>
      <div className="flex flex-col gap-3">
        <DNABar label="Doc A" stats={statsA} color="var(--amber)" />
        <DNABar label="Doc B" stats={statsB} color="var(--terra)" />
      </div>
      {overlap > 0 && (
        <p className="font-mono" style={{ fontSize: 11, color: "var(--ink-secondary)", marginTop: 12 }}>
          These documents share ~{overlap}% vocabulary overlap
        </p>
      )}
    </div>
  );
}

function DNABar({ label, stats, color }) {
  return (
    <div className="flex items-center gap-3">
      <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-tertiary)", width: 40 }}>{label}</span>
      <div style={{ flex: 1, height: 8, background: "var(--bg-elevated)", borderRadius: 4, overflow: "hidden" }}>
        <div style={{
          height: "100%", borderRadius: 4, background: color,
          width: `${Math.min(stats.complexity, 100)}%`,
          transition: "width 600ms var(--ease)",
        }} />
      </div>
      <span className="font-mono" style={{ fontSize: 10, color: "var(--ink-tertiary)", width: 60, textAlign: "right" }}>
        {stats.words} words
      </span>
    </div>
  );
}

function computeDocStats(text) {
  const words = text.trim().split(/\s+/).filter(Boolean);
  const avgWordLen = words.length > 0 ? words.reduce((s, w) => s + w.length, 0) / words.length : 0;
  return {
    words: words.length,
    complexity: Math.min(avgWordLen * 15, 100),
  };
}

/* ── Doc Input Card ── */
function DocInputCard({ label, value, onChange, placeholder, onRemove, accentColor }) {
  return (
    <div className="card" style={{ overflow: "hidden" }}>
      <div className="flex items-center justify-between" style={{
        padding: "12px 16px", borderBottom: "1px solid var(--border-dim)",
      }}>
        <h4 className="font-body" style={{ fontSize: 14, fontWeight: 600, color: "var(--ink-primary)", margin: 0 }}>
          <span style={{ color: accentColor, marginRight: 6 }}>●</span>
          {label}
        </h4>
        {onRemove && (
          <button onClick={onRemove} className="btn-ghost" style={{ padding: "4px 8px", fontSize: 12 }}>×</button>
        )}
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="font-body"
        style={{
          width: "100%", resize: "none", outline: "none", border: "none",
          fontSize: 14, lineHeight: 1.75, padding: "16px",
          background: "transparent", color: "var(--ink-primary)",
          minHeight: 200,
        }}
      />
      <div style={{ padding: "8px 16px", borderTop: "1px solid var(--border-dim)" }}>
        <span className="font-mono" style={{ fontSize: 11, color: "var(--ink-tertiary)" }}>
          {value.trim().split(/\s+/).filter(Boolean).length} words
        </span>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   SYNTHESIS WORKSPACE
   ═══════════════════════════════════════════════════ */
export default function SynthesisWorkspace() {
  const { auth } = useAppContext();
  const user = auth?.user;

  const [docA, setDocA] = useState("");
  const [docB, setDocB] = useState("");
  const [docC, setDocC] = useState("");
  const [showDocC, setShowDocC] = useState(false);
  const [synthesisMode, setSynthesisMode] = useState("unified");
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [documentIds, setDocumentIds] = useState("");

  async function handleSynthesize() {
    if (!documentIds.trim()) {
      setError("Enter at least one Document ID to synthesize.");
      return;
    }
    setLoading(true); setError(null); setResult(null);
    try {
      const idsArray = documentIds.split(",").map(id => parseInt(id.trim(), 10)).filter(id => !isNaN(id));
      if (idsArray.length === 0) throw new Error("No valid document IDs found.");
      const res = await synthesizeDocuments(idsArray, prompt.trim() || null);
      setResult(res.summary);
    } catch (err) {
      setError(`Synthesis failed: ${err.message}`);
    } finally { setLoading(false); }
  }

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center text-center" style={{ padding: "80px 32px" }}>
        <div style={{
          width: 64, height: 64, borderRadius: 16,
          background: "var(--bg-elevated)", border: "1px solid var(--border-dim)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 28, marginBottom: 24,
        }}>⊞</div>
        <h3 className="font-body" style={{ fontSize: 16, fontWeight: 600, color: "var(--ink-primary)", marginBottom: 8 }}>
          Sign in to use Multi-Doc Synthesis
        </h3>
        <p className="font-body" style={{ fontSize: 13, color: "var(--ink-tertiary)", maxWidth: 320 }}>
          Compare sources and distil insights across multiple ingested documents.
        </p>
      </div>
    );
  }

  return (
    <div className="animate-in">
      {error && (
        <div className="flex items-center gap-2 animate-in" style={{
          padding: "12px 16px", borderRadius: "var(--radius-btn)", marginBottom: 16,
          background: "rgba(224,92,92,0.08)", border: "1px solid rgba(224,92,92,0.2)",
          fontSize: 13, color: "var(--rose)",
        }}>
          <span>⚠</span> {error}
        </div>
      )}

      {/* Synthesis Mode Selector */}
      <div style={{ marginBottom: 24 }}>
        <p className="section-header" style={{ marginBottom: 12 }}>Synthesis Mode</p>
        <div className="mode-selector">
          {SYNTHESIS_MODES.map((m) => (
            <button
              key={m.value}
              onClick={() => setSynthesisMode(m.value)}
              className={`mode-card ${synthesisMode === m.value ? "active" : ""}`}
              style={{ minWidth: 140 }}
            >
              <span className="mode-icon">{m.icon}</span>
              <span className="mode-label">{m.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Document DNA */}
      <DocumentDNA docA={docA} docB={docB} />

      {/* Documents Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: showDocC ? "1fr 1fr 1fr" : "1fr 1fr",
        gap: 16, marginBottom: 16,
      }}>
        <DocInputCard label="Document A" value={docA} onChange={setDocA} placeholder="Paste first document text..." accentColor="var(--amber)" />
        <DocInputCard label="Document B" value={docB} onChange={setDocB} placeholder="Paste second document text..." accentColor="var(--terra)" />
        {showDocC && (
          <DocInputCard
            label="Document C" value={docC} onChange={setDocC}
            placeholder="Paste third document text..."
            onRemove={() => { setShowDocC(false); setDocC(""); }}
            accentColor="var(--sky)"
          />
        )}
      </div>

      {!showDocC && (
        <button onClick={() => setShowDocC(true)} className="btn-ghost" style={{ marginBottom: 16, color: "var(--amber)" }}>
          + Add 3rd Document
        </button>
      )}

      {/* Document IDs + Prompt */}
      <div className="card" style={{ padding: 20, marginBottom: 16 }}>
        <div className="flex gap-4 flex-wrap">
          <div style={{ flex: 1, minWidth: 200 }}>
            <p className="section-header" style={{ marginBottom: 8 }}>Document IDs (comma-separated)</p>
            <input
              type="text" value={documentIds}
              onChange={(e) => setDocumentIds(e.target.value)}
              placeholder="e.g. 1, 4, 7"
              className="font-mono w-full"
              style={{
                background: "var(--bg-input)", border: "1px solid var(--border-dim)",
                borderRadius: "var(--radius-input)", padding: "10px 14px",
                fontSize: 13, color: "var(--ink-primary)", outline: "none",
              }}
            />
          </div>
          <div style={{ flex: 1, minWidth: 200 }}>
            <p className="section-header" style={{ marginBottom: 8 }}>Custom Prompt (optional)</p>
            <input
              type="text" value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Compare the main arguments"
              className="font-body w-full"
              style={{
                background: "var(--bg-input)", border: "1px solid var(--border-dim)",
                borderRadius: "var(--radius-input)", padding: "10px 14px",
                fontSize: 13, color: "var(--ink-primary)", outline: "none",
              }}
            />
          </div>
        </div>
      </div>

      {/* Synthesize Button */}
      <div className="flex justify-end" style={{ marginBottom: 24 }}>
        <button
          onClick={handleSynthesize}
          disabled={loading || !documentIds.trim()}
          className="btn-primary"
          style={{ height: 44, minWidth: 180 }}
        >
          {loading ? (
            <>
              <span style={{
                width: 14, height: 14, border: "2px solid rgba(11,9,6,0.3)",
                borderTopColor: "#0B0906", borderRadius: "50%",
                animation: "spin 600ms linear infinite", display: "inline-block",
              }} />
              Synthesizing...
            </>
          ) : (
            <>Synthesize →</>
          )}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="card anim-output-reveal" style={{ padding: 24 }}>
          <p className="section-header" style={{ marginBottom: 16 }}>Synthesis Result</p>
          <div className="font-body" style={{ fontSize: 15, lineHeight: 1.7, color: "var(--ink-primary)" }}>
            {result.split('\n').map((line, i) => (
              <p key={i} style={{ margin: "0 0 8px" }}>{line}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
