/**
 * Provider status — pings backend health endpoint to determine
 * live/degraded/offline state. Re-pings every 60 seconds.
 */
import { useState, useEffect, useCallback, useRef } from "react";
import { config } from "../config.js";

const PING_INTERVAL = 60000; // 60 seconds
const DEGRADED_THRESHOLD = 800; // ms
const TIMEOUT_THRESHOLD = 2000; // ms

export function useProviderStatus() {
  const [status, setStatus] = useState("live"); // 'live' | 'degraded' | 'offline'
  const [label, setLabel] = useState("");
  const [latency, setLatency] = useState(null);
  const intervalRef = useRef(null);

  const ping = useCallback(async () => {
    const start = performance.now();
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_THRESHOLD);

    try {
      const res = await fetch(`${config.apiBaseUrl.replace(/\/$/, "")}/`, {
        method: "GET",
        signal: controller.signal,
        credentials: "include",
      });
      clearTimeout(timeout);
      const elapsed = performance.now() - start;
      setLatency(Math.round(elapsed));

      if (!res.ok) {
        setStatus("offline");
        setLabel("Offline");
        return;
      }

      const data = await res.json().catch(() => null);
      const providerName = data?.mode || "groq";

      if (elapsed < DEGRADED_THRESHOLD) {
        setStatus("live");
        setLabel(`Live · ${providerName}`);
      } else {
        setStatus("degraded");
        setLabel("Degraded");
      }
    } catch {
      clearTimeout(timeout);
      setStatus("offline");
      setLabel("Offline");
      setLatency(null);
    }
  }, []);

  useEffect(() => {
    ping();
    intervalRef.current = setInterval(ping, PING_INTERVAL);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [ping]);

  return { status, label, latency };
}
