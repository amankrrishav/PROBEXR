import { useState, useEffect, useRef, useCallback } from "react";

/**
 * CustomCursor — Amber dot cursor that expands on interactive element hover.
 * Desktop only; disabled on touch/mobile devices.
 */
export default function CustomCursor() {
  const cursorRef = useRef(null);
  const [hovering, setHovering] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Disable on touch devices
    if ("ontouchstart" in window || navigator.maxTouchPoints > 0) return;
    if (window.innerWidth < 768) return;

    // Hide default cursor
    document.body.style.cursor = "none";
    requestAnimationFrame(() => setVisible(true));

    const move = (e) => {
      if (cursorRef.current) {
        cursorRef.current.style.left = e.clientX + "px";
        cursorRef.current.style.top = e.clientY + "px";
      }
    };

    const interactiveTags = new Set(["A", "BUTTON", "INPUT", "TEXTAREA", "SELECT", "LABEL"]);

    const enter = (e) => {
      if (interactiveTags.has(e.target.tagName) || e.target.closest("button, a, input, textarea, select, [role='button']")) {
        setHovering(true);
      }
    };
    const leave = (e) => {
      if (interactiveTags.has(e.target.tagName) || e.target.closest("button, a, input, textarea, select, [role='button']")) {
        setHovering(false);
      }
    };

    document.addEventListener("mousemove", move, { passive: true });
    document.addEventListener("mouseenter", enter, true);
    document.addEventListener("mouseleave", leave, true);
    document.addEventListener("mouseover", enter, { passive: true });
    document.addEventListener("mouseout", leave, { passive: true });

    return () => {
      document.body.style.cursor = "";
      document.removeEventListener("mousemove", move);
      document.removeEventListener("mouseenter", enter, true);
      document.removeEventListener("mouseleave", leave, true);
      document.removeEventListener("mouseover", enter);
      document.removeEventListener("mouseout", leave);
    };
  }, []);

  if (!visible) return null;

  return (
    <div
      ref={cursorRef}
      className={`custom-cursor${hovering ? " hovering" : ""}`}
    />
  );
}
