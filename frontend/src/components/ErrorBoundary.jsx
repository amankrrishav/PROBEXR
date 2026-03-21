import React from "react";

/**
 * ErrorBoundary — Catches unhandled component errors and shows a styled
 * fallback using the project's CSS variable design system.
 * Prevents the entire app from crashing to a white screen.
 */
export class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error("[ErrorBoundary] Caught:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{
                    display: "flex", flexDirection: "column", alignItems: "center",
                    justifyContent: "center", minHeight: "60vh", padding: 40,
                    textAlign: "center",
                }}>
                    <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.6 }}>⚠️</div>
                    <h2 className="font-display" style={{
                        fontSize: 24, color: "var(--ink-primary)", marginBottom: 8,
                    }}>
                        Something went wrong
                    </h2>
                    <p className="font-body" style={{
                        fontSize: 14, color: "var(--ink-secondary)",
                        maxWidth: 400, marginBottom: 24,
                    }}>
                        {this.state.error?.message || "An unexpected error occurred. Try refreshing the page."}
                    </p>
                    <button
                        onClick={() => this.setState({ hasError: false, error: null })}
                        style={{
                            padding: "10px 24px", borderRadius: 8, border: "none",
                            background: "var(--amber)", color: "var(--bg-base)",
                            fontSize: 14, fontWeight: 600, cursor: "pointer",
                            transition: "all 0.2s ease", marginRight: 8,
                        }}
                    >
                        Try Again
                    </button>
                    <button
                        onClick={() => window.location.reload()}
                        style={{
                            padding: "10px 24px", borderRadius: 8,
                            border: "1px solid var(--border-dim)", background: "transparent",
                            color: "var(--ink-secondary)", fontSize: 14,
                            cursor: "pointer", transition: "all 0.2s ease",
                        }}
                    >
                        Reload Page
                    </button>
                </div>
            );
        }
        return this.props.children;
    }
}
