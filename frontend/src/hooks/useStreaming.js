/**
 * useStreaming — streaming state and abort controller management.
 *
 * Owns: streaming flag, accumulated streamingText, and abort logic.
 */
import { useState, useCallback, useRef } from "react";

export function useStreaming() {
  const [streaming, setStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const abortControllerRef = useRef(null);

  const cancelStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStreaming(false);
  }, []);

  const resetStreaming = useCallback(() => {
    cancelStreaming();
    setStreamingText("");
  }, [cancelStreaming]);

  return {
    streaming, setStreaming,
    streamingText, setStreamingText,
    abortControllerRef,
    cancelStreaming,
    resetStreaming,
  };
}
