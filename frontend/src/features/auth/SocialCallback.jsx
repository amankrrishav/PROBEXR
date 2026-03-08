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

  return (
    <div className="fixed inset-0 z-[60] flex flex-col items-center justify-center bg-white dark:bg-[#0a0a0a]">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-black border-t-transparent dark:border-white" />
      <p className="mt-4 text-sm font-medium">{status}</p>
    </div>
  );
}
