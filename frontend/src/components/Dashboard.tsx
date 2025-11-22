import React from "react";
import MeshView from "./MeshView";
import CameraFeed from "./CameraFeed"; // Import CameraFeed
import { TriageOutput } from "../ws";

type DashboardProps = {
  presageSummary: Record<string, any>;
  audioSummary: Record<string, any>;
  triageOutput?: TriageOutput;
  connectionStatus: "connecting" | "open" | "closed";
  isSimulated: boolean; // New prop
};

const formatNumber = (v: any, digits = 1) =>
  typeof v === "number" ? v.toFixed(digits) : "–";

const statusColor = (status: DashboardProps["connectionStatus"]) => {
  if (status === "open") return "#43a047";
  if (status === "connecting") return "#fbc02d";
  return "#e53935";
};

export const Dashboard: React.FC<DashboardProps> = ({
  presageSummary,
  audioSummary,
  triageOutput,
  connectionStatus,
  isSimulated, // Destructure new prop
}) => {
  const alertActive = (triageOutput?.triage_level || 1) >= 4;
  const highlight = triageOutput?.ui_directives?.highlight_regions || [];

  return (
    <div className="card" style={{ position: "relative" }}>
      <div className={`alert-overlay ${alertActive ? "active" : ""}`} style={{ background: triageOutput?.ui_directives?.alert_color || "#43a047" }} />
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ margin: 0 }}>Neuro-Sentry Dashboard</h2>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}> {/* Added a div for flexible spacing */}
          {isSimulated && (
            <span className="status-chip" style={{ backgroundColor: "#ffc107", color: "#333" }}>
              SIMULATED
            </span>
          )}
          <span className="status-chip" style={{ color: statusColor(connectionStatus) }}>
            <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: statusColor(connectionStatus) }} />
            {connectionStatus}
          </span>
        </div>
      </div>

      <div className="row" style={{ marginTop: 12 }}>
        <div style={{ flex: 2, minWidth: 320, position: "relative" }}> {/* Added position: "relative" */}
          <CameraFeed /> {/* Added CameraFeed component */}
          <MeshView
            points={(presageSummary?.face_points as number[][]) || []}
            highlightRegions={highlight as string[]}
          />
        </div>
        <div style={{ flex: 1, minWidth: 240 }} className="card">
          <h3 style={{ marginTop: 0 }}>Vitals</h3>
          <div>Heart rate: {formatNumber(presageSummary?.heart_rate)} bpm</div>
          <div>Breathing: {formatNumber(presageSummary?.breathing_rate)} rpm</div>
          <div>Quality: {formatNumber(presageSummary?.quality)}</div>
          <div>Points: {presageSummary?.point_count ?? 0}</div>
          <div style={{ marginTop: 8, fontSize: 12, opacity: 0.8 }}>
            Window: {presageSummary?.window_seconds ?? 0}s | Samples: {presageSummary?.count ?? 0}
          </div>
        </div>
      </div>

      <div className="row" style={{ marginTop: 14 }}>
        <div className="card" style={{ flex: 1 }}>
          <h3 style={{ marginTop: 0 }}>Audio Features</h3>
          <div>Energy: {formatNumber(audioSummary?.energy, 4)}</div>
          <div>Jitter: {formatNumber(audioSummary?.jitter, 4)}</div>
          <div>Shimmer: {formatNumber(audioSummary?.shimmer, 4)}</div>
          <div>Duration: {formatNumber(audioSummary?.duration, 2)}s</div>
        </div>

        <div className="card" style={{ flex: 1 }}>
          <h3 style={{ marginTop: 0 }}>Triage</h3>
          <div>Risk: {formatNumber(triageOutput?.overall_risk, 3)}</div>
          <div>Level: {triageOutput?.triage_level ?? "–"}</div>
          <div>Confidence: {formatNumber(triageOutput?.confidence, 3)}</div>
          <div style={{ marginTop: 8, fontSize: 13, opacity: 0.8 }}>
            {triageOutput?.rationale_short || "Waiting for live data..."}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
