import { useEffect, useState } from "react";

export default function DifficultyBar({ score = 0, color = "#6366f1" }) {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    // Clamp score between 0–10
    const safeScore = Math.max(0, Math.min(10, score));

    const timer = setTimeout(() => {
      setWidth((safeScore / 10) * 100);
    }, 150);

    return () => clearTimeout(timer);
  }, [score]);

  return (
    <div
      style={{
        height: "8px",
        background: "#f0eeea",
        borderRadius: "99px",
        overflow: "hidden",
        marginTop: "12px",
      }}
    >
      <div
        style={{
          height: "100%",
          width: `${width}%`,
          backgroundColor: color,
          transition: "width 0.9s cubic-bezier(0.22, 1, 0.36, 1)",
        }}
      />
    </div>
  );
}