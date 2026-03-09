import { useState } from "react";
import { useAppContext } from "../../contexts/AppContext.jsx";
import { synthesizeDocuments } from "../../services/api";

const SYNTHESIS_MODES = [
  { value: "unified", label: "Unified Summary", icon: "⊞" },
  { value: "compare", label: "Compare & Contrast", icon: "⇔" },
  { value: "disagreements", label: "Key Disagreements", icon: "⚡" },
  { value: "timeline", label: "Timeline Merge", icon: "⟿" },
];

function DocInputCard({ label, value, onChange, placeholder, onRemove }) {
  return (
    <div className="card" style={{ overflow: "hidden" }}>
      <div className="flex items-center justify-between" style={{
        padding: "12px 16px", borderBottom: "1px solid var(--border)",
      }}>
        <h4 className="font-display" style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
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
        className="font-mono"
        style={{
          width: "100%", resize: "none", outline: "none", border: "none",
          fontSize: 13, lineHeight: 1.8, padding: "16px",
          background: "transparent", color: "var(--text-primary)",
          minHeight: 180,
        }}
      />
      <div style={{ padding: "8px 16px", borderTop: "1px solid var(--border)" }}>
        <span className="font-mono" style={{ fontSize: 11, color: "var(--text-tertiary)" }}>
          {value.trim().split(/\s+/).filter(Boolean).length} words
        </span>
      </div>
    </div>
  );
}

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

  // For now, the API expects document IDs. We'll use a text-based local approach.
  // TODO: integrate with backend document synthesis when text-based endpoint is available
  const [documentIds, setDocumentIds] = useState("");

  async function handleSynthesize() {
    if (!documentIds.trim()) {
      setError("Enter at least one Document ID to synthesize.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const idsArray = documentIds.split(",").map(id => parseInt(id.trim(), 10)).filter(id => !isNaN(id));
      if (idsArray.length === 0) throw new Error("No valid document IDs found.");
      const res = await synthesizeDocuments(idsArray, prompt.trim() || null);
      setResult(res.summary);
    } catch (err) {
      setError(`Synthesis failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center text-center" style={{ padding: "80px 32px" }}>
        <div style={{
          width: 64, height: 64, borderRadius: 16,
          background: "var(--bg-elevated)", border: "1px solid var(--border)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 28, marginBottom: 24,
        }}>⊞</div>
        <h3 className="font-body" style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>
          Sign in to use Multi-Doc Synthesis
        </h3>
        <p className="font-body" style={{ fontSize: 13, color: "var(--text-tertiary)", maxWidth: 320 }}>
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
          background: "rgba(255,107,107,0.08)", border: "1px solid rgba(255,107,107,0.2)",
          fontSize: 13, color: "var(--accent-warn)",
        }}>
          <span>⚠</span> {error}
        </div>
      )}

      {/* Synthesis Mode Selector */}
      <div style={{ marginBottom: 24 }}>
        <p className="section-header" style={{ marginBottom: 12 }}>Synthesis Mode</p>
        <div className="flex gap-2 flex-wrap">
          {SYNTHESIS_MODES.map((m) => (
            <button
              key={m.value}
              onClick={() => setSynthesisMode(m.value)}
              className={`mode-card ${synthesisMode === m.value ? "active" : ""}`}
              style={{ flex: "1 1 auto", minWidth: 140 }}
            >
              <span className="mode-icon">{m.icon}</span>
              <span className="mode-label">{m.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Documents Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: showDocC ? "1fr 1fr 1fr" : "1fr 1fr",
        gap: 16, marginBottom: 16,
      }}>
        <DocInputCard label="Document A" value={docA} onChange={setDocA} placeholder="Paste first document text..." />
        <DocInputCard label="Document B" value={docB} onChange={setDocB} placeholder="Paste second document text..." onRemove={null} />
        {showDocC && (
          <DocInputCard
            label="Document C" value={docC} onChange={setDocC}
            placeholder="Paste third document text..."
            onRemove={() => { setShowDocC(false); setDocC(""); }}
          />
        )}
      </div>

      {!showDocC && (
        <button onClick={() => setShowDocC(true)} className="btn-ghost" style={{ marginBottom: 16, color: "var(--accent)" }}>
          + Add 3rd Document
        </button>
      )}

      {/* Document IDs + Prompt (for API) */}
      <div className="card" style={{ padding: 20, marginBottom: 16 }}>
        <div className="flex gap-4 flex-wrap">
          <div style={{ flex: 1, minWidth: 200 }}>
            <p className="section-header" style={{ marginBottom: 8 }}>Document IDs (comma-separated)</p>
            <input
              type="text"
              value={documentIds}
              onChange={(e) => setDocumentIds(e.target.value)}
              placeholder="e.g. 1, 4, 7"
              className="font-mono w-full"
              style={{
                background: "var(--bg-input)", border: "1px solid var(--border)",
                borderRadius: "var(--radius-input)", padding: "10px 14px",
                fontSize: 13, color: "var(--text-primary)", outline: "none",
              }}
            />
          </div>
          <div style={{ flex: 1, minWidth: 200 }}>
            <p className="section-header" style={{ marginBottom: 8 }}>Custom Prompt (optional)</p>
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Compare the main arguments"
              className="font-body w-full"
              style={{
                background: "var(--bg-input)", border: "1px solid var(--border)",
                borderRadius: "var(--radius-input)", padding: "10px 14px",
                fontSize: 13, color: "var(--text-primary)", outline: "none",
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
          style={{ height: 44, minWidth: 180, background: "var(--gradient-hero)" }}
        >
          {loading ? (
            <>
              <span style={{
                width: 14, height: 14, border: "2px solid rgba(255,255,255,0.3)",
                borderTopColor: "white", borderRadius: "50%",
                animation: "spin 600ms linear infinite", display: "inline-block",
              }} />
              Synthesizing...
            </>
          ) : (
            <>Synthesize <span>→</span></>
          )}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="card animate-in" style={{ padding: 24 }}>
          <p className="section-header" style={{ marginBottom: 16 }}>Synthesis Result</p>
          <div className="font-body" style={{ fontSize: 15, lineHeight: 1.7, color: "var(--text-primary)" }}>
            {result.split('\n').map((line, i) => (
              <p key={i} style={{ margin: "0 0 8px" }}>{line}</p>
            ))}
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        input::placeholder { color: var(--text-tertiary); }
        textarea::placeholder { color: var(--text-tertiary); }
      `}</style>
    </div>
  );
}
