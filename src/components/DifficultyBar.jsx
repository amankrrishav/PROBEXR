import { useEffect, useState } from "react";

export default function DifficultyBar({ score }) {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setWidth((score / 10) * 100);
    }, 150);
    return () => clearTimeout(timer);
  }, [score]);

  return (
    <div style={{
      height: "8px",
      background: "#f0eeea",
      borderRadius: "99px",
      overflow: "hidden",
      marginTop: "12px"
    }}>
      <div
        style={{
          height: "100%",
          width: `${width}%`,
          backgroundColor: "#6366f1",
          transition: "width 0.9s cubic-bezier(0.22, 1, 0.36, 1)"
        }}
      />
    </div>
  );
}