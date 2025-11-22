import React from "react";

type MeshViewProps = {
  points?: number[][];
  highlightRegions?: string[];
};

const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

export const MeshView: React.FC<MeshViewProps> = ({ points = [], highlightRegions = [] }) => {
  return (
    <div className="mesh-canvas card">
      {points.slice(0, 120).map((p, idx) => {
        const [x = 0.5, y = 0.5] = p;
        const left = clamp01(x) * 100;
        const top = clamp01(y) * 100;
        return (
          <div
            key={`${idx}-${left}-${top}`}
            className="mesh-point"
            style={{ left: `${left}%`, top: `${top}%` }}
          />
        );
      })}

      {highlightRegions.length > 0 && (
        <div
          style={{
            position: "absolute",
            bottom: 10,
            right: 10,
            background: "rgba(0,0,0,0.45)",
            padding: "6px 10px",
            borderRadius: 8,
            fontSize: 12,
          }}
        >
          Highlight: {highlightRegions.join(", ")}
        </div>
      )}
    </div>
  );
};

export default MeshView;
