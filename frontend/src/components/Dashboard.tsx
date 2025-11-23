import React from "react";
import { GeminiReport, LiveVitals } from "../ws";

type Props = {
  liveVitals: LiveVitals | null;
  rawPackets: Record<string, unknown>[];
  geminiReport: GeminiReport | null;
  connectionStatus: "connecting" | "open" | "closed";
};

const statusColor = (status: Props["connectionStatus"]) => {
  if (status === "open") return "#43a047";
  if (status === "connecting") return "#fbc02d";
  return "#e53935";
};

const fmt = (value: number | null | undefined, digits = 1) =>
  value === null || value === undefined || Number.isNaN(value) ? "—" : Number(value).toFixed(digits);

const LivePanel: React.FC<{ vitals: LiveVitals | null }> = ({ vitals }) => (
  <div className="card">
    <h3 style={{ marginTop: 0 }}>Live Vitals</h3>
    {vitals ? (
      <div className="row" style={{ justifyContent: "space-around", textAlign: "center" }}>
        <div>
          <div className="stat-big">{fmt(vitals.heart_rate)}</div>
          <div className="stat-label">Heart Rate</div>
        </div>
        <div>
          <div className="stat-big">{fmt(vitals.breathing_rate)}</div>
          <div className="stat-label">Breathing</div>
        </div>
        <div>
          <div className="stat-big">{fmt((vitals.quality ?? 0) * 100, 0)}%</div>
          <div className="stat-label">Signal Quality</div>
        </div>
      </div>
    ) : (
      <div style={{ opacity: 0.7 }}>Waiting for Presage packets...</div>
    )}
    <div style={{ fontSize: 12, opacity: 0.8, marginTop: 8 }}>
      Packets this session: {vitals?.session_packet_count ?? 0}
    </div>
  </div>
);

const GeminiPanel: React.FC<{ report: GeminiReport | null }> = ({ report }) => (
  <div className="card">
    <h3 style={{ marginTop: 0 }}>Gemini Triage</h3>
    {report ? (
      <>
        <div className="row" style={{ gap: 16 }}>
          <div>
            <div style={{ fontSize: 12, opacity: 0.8 }}>Risk</div>
            <div style={{ fontSize: 24, fontWeight: 800 }}>{report.risk_level}</div>
          </div>
          <div>
            <div style={{ fontSize: 12, opacity: 0.8 }}>Stroke Probability</div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>{fmt(report.stroke_probability * 100, 1)}%</div>
          </div>
          {report.bell_palsy_probability !== undefined && (
            <div>
              <div style={{ fontSize: 12, opacity: 0.8 }}>Bell's Probability</div>
              <div style={{ fontSize: 22, fontWeight: 700 }}>{fmt(report.bell_palsy_probability * 100, 1)}%</div>
            </div>
          )}
          <div>
            <div style={{ fontSize: 12, opacity: 0.8 }}>Confidence</div>
            <div style={{ fontSize: 20, fontWeight: 700 }}>{fmt(report.confidence, 2)}</div>
          </div>
        </div>
        <div style={{ marginTop: 10, fontSize: 14, lineHeight: 1.4 }}>{report.summary}</div>
        <div style={{ marginTop: 6, fontSize: 13, opacity: 0.9 }}>
          Recommendation: {report.recommendation}
        </div>
        <pre style={{ marginTop: 10, padding: 10, background: "rgba(0,0,0,0.25)", borderRadius: 8, fontSize: 12 }}>
{JSON.stringify(report, null, 2)}
        </pre>
      </>
    ) : (
      <div style={{ opacity: 0.7 }}>Final Gemini report will appear after session_end.</div>
    )}
  </div>
);

const RawDumpPanel: React.FC<{ packets: Record<string, unknown>[] }> = ({ packets }) => (
  <div className="card">
    <h3 style={{ marginTop: 0 }}>Raw Packet Dump</h3>
    <div style={{ fontSize: 12, opacity: 0.8, marginBottom: 6 }}>Total packets: {packets.length}</div>
    <pre style={{ maxHeight: 320, overflow: "auto", background: "rgba(0,0,0,0.3)", padding: 10, borderRadius: 8, fontSize: 12 }}>
{packets.length ? JSON.stringify(packets, null, 2) : "No packets yet. Start a session to see live data."}
    </pre>
  </div>
);

const Dashboard: React.FC<Props> = ({ liveVitals, rawPackets, geminiReport, connectionStatus }) => {
  return (
    <div className="dashboard">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 style={{ margin: 0 }}>Neuro-Sentry</h2>
          <div style={{ fontSize: 13, opacity: 0.75 }}>Live Presage → FastAPI → Gemini</div>
        </div>
        <span className="status-chip" style={{ color: statusColor(connectionStatus) }}>
          <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: statusColor(connectionStatus) }} />
          {connectionStatus === "open" ? "LIVE" : connectionStatus === "connecting" ? "CONNECTING" : "DISCONNECTED"}
        </span>
      </div>

      <div className="row" style={{ marginTop: 12, gap: 12 }}>
        <div style={{ flex: 1, minWidth: 260 }}>
          <LivePanel vitals={liveVitals} />
        </div>
        <div style={{ flex: 1, minWidth: 260 }}>
          <GeminiPanel report={geminiReport} />
        </div>
      </div>

      <div style={{ marginTop: 12 }}>
        <RawDumpPanel packets={rawPackets} />
      </div>
    </div>
  );
};

export default Dashboard;
