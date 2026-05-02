import { useEffect, useState } from "react";
import { useAppContext } from "../../contexts/AppContext";
import { config } from "../../config";

export default function SocialCallback({ provider, onResult }) {
  const { auth } = useAppContext();
  const [status, setStatus] = useState("Authenticating...");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code") || params.get("token");

    if (!code) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- error handling during mount
      setStatus("Error: No authentication token received.");
      onResult?.(false);
      return;
    }

    async function exchangeCode() {
      try {
        const endpoint = provider === "verify" ? "/auth/verify" : `/auth/${provider}/callback`;
        const method = provider === "verify" ? "GET" : "POST";
        const url = new URL(`${config.apiBaseUrl}${endpoint}`);
        if (method === "GET") url.searchParams.set("token", code);

        const resp = await fetch(url.toString(), {
          method,
          headers: method === "POST" ? { "Content-Type": "application/json" } : {},
          body: method === "POST" ? JSON.stringify({ code }) : null,
        });

        if (!resp.ok) {
          const data = await resp.json();
          throw new Error(data.detail || "Social authentication failed.");
        }

        const data = await resp.json();
        // The backend sets the auth cookies, but we might need to refresh local state
        await auth.refreshUser();
        setStatus("Success! Redirecting...");
        onResult?.(true);
      } catch (err) {
        setStatus(`Error: ${err.message}`);
        onResult?.(false);
      }
    }

    exchangeCode();
  }, [provider, auth, onResult]);

  const isError = status.startsWith("Error");

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 200,
      display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      background: "var(--bg-base)",
    }}>
      {!isError && (
        <div style={{
          width: 32, height: 32,
          border: "2px solid var(--border-dim)",
          borderTopColor: "var(--amber)",
          borderRadius: "50%",
          animation: "spin 600ms linear infinite",
        }} />
      )}
      {isError && (
        <div style={{
          width: 40, height: 40, borderRadius: "50%",
          background: "rgba(224,92,92,0.1)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 18,
        }}>⚠</div>
      )}
      <p className="font-body" style={{
        marginTop: 16, fontSize: 14, fontWeight: 500,
        color: isError ? "var(--rose)" : "var(--ink-primary)",
      }}>
        {status}
      </p>
    </div>
  );
}