import React from "react";

type DashboardProps = {
  liveData: Record<string, any> | null;
  rawPackets: Record<string, unknown>[];
  connectionStatus: "connecting" | "open" | "closed";
  finalReport?: Record<string, unknown> | null;
};

const statusColor = (status: DashboardProps["connectionStatus"]) => {
  if (status === "open") return "#43a047";
  if (status === "connecting") return "#fbc02d";
  return "#e53935";
};

const LiveVitals: React.FC<{ data: Record<string, any> }> = ({ data }) => (
  <div className="card" style={{ marginBottom: 12, background: "linear-gradient(to right, #1e3c72, #2a5298)" }}>
    <h3 style={{ marginTop: 0, color: "#e0e0e0" }}>Live Vitals</h3>
    <div className="row" style={{ justifyContent: "space-around", textAlign: "center" }}>
      <div>
        <div style={{ fontSize: 24, fontWeight: "bold", color: "white" }}>
          {data.heart_rate ? data.heart_rate.toFixed(1) : "--"}
        </div>
        <div style={{ fontSize: 12, color: "#b0bec5" }}>Heart Rate</div>
      </div>
      <div>
        <div style={{ fontSize: 24, fontWeight: "bold", color: "white" }}>
          {data.breathing_rate ? data.breathing_rate.toFixed(1) : "--"}
        </div>
        <div style={{ fontSize: 12, color: "#b0bec5" }}>Breathing Rate</div>
      </div>
      <div>
        <div style={{ fontSize: 24, fontWeight: "bold", color: "white" }}>
          {data.quality ? (data.quality * 100).toFixed(0) + "%" : "--"}
        </div>
        <div style={{ fontSize: 12, color: "#b0bec5" }}>Signal Quality</div>
      </div>
    </div>
    <div style={{textAlign: 'center', marginTop: '10px', fontSize: 12, color: '#b0bec5'}}>Packets: {data.session_packet_count}</div>
  </div>
);

export const Dashboard: React.FC<DashboardProps> = ({
  liveData,
  rawPackets,
  connectionStatus,
  finalReport,
}) => {
  return (
    <div className="card" style={{ position: "relative" }}>
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ margin: 0 }}>Neuro-Sentry Dashboard</h2>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="status-chip" style={{ color: statusColor(connectionStatus) }}>
            <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: statusColor(connectionStatus) }} />
            {connectionStatus === "open" ? "LIVE" : "DISCONNECTED"}
          </span>
        </div>
      </div>

      {liveData && <LiveVitals data={liveData} />}

      <div className="card" style={{ marginTop: 12 }}>
        <h3 style={{ marginTop: 0 }}>Raw Session Dump</h3>
        <div style={{ fontSize: 13, opacity: 0.85, marginBottom: 6 }}>
          Total Packets Recorded: {rawPackets.length}
        </div>
        <pre style={{ maxHeight: 320, overflow: "auto", background: "rgba(0,0,0,0.3)", padding: 10, borderRadius: 8, fontSize: 12 }}>
          {rawPackets.length > 0 ? JSON.stringify(rawPackets, null, 2) : "Waiting for session to end..."}
        </pre>
      </div>

      {finalReport && (
        <div className="card" style={{ marginTop: 14, border: "1px solid #4fc3f7" }}>
          <h3 style={{ marginTop: 0 }}>Final Analysis (Gemini)</h3>
          <div><strong>Risk Level:</strong> {(finalReport["risk_level"] as string) || "—"}</div>
          <div><strong>Stroke Probability:</strong> {finalReport["stroke_probability"] != null ? `${(Number(finalReport["stroke_probability"]) * 100).toFixed(1)}%` : "—"}</div>
          <div><strong>Confidence:</strong> {finalReport["confidence"] != null ? (finalReport["confidence"] as number).toFixed(2) : "—"}</div>
          <div style={{ marginTop: 6 }}><strong>Summary:</strong> {(finalReport["summary"] as string) || "No summary"}</div>
          <div style={{ marginTop: 6, fontSize: 13, opacity: 0.9 }}>
            <strong>Recommendation:</strong> {(finalReport["recommendation"] as string) || "No recommendation"}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
