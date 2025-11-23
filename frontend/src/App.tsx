import React, { useEffect, useState } from "react";
import Dashboard from "./components/Dashboard";
import { GeminiReport, LiveStateMessage, LiveVitals, connectLiveState } from "./ws";

const App: React.FC = () => {
  const [liveVitals, setLiveVitals] = useState<LiveVitals | null>(null);
  const [rawPackets, setRawPackets] = useState<Record<string, unknown>[]>([]);
  const [geminiReport, setGeminiReport] = useState<GeminiReport | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<"connecting" | "open" | "closed">("connecting");

  useEffect(() => {
    const disconnect = connectLiveState({
      onMessage: (payload: LiveStateMessage) => {
        switch (payload.type) {
          case "live":
            setLiveVitals(payload.data);
            if (payload.data.session_packet_count === 1) {
              setRawPackets([]);
              setGeminiReport(null);
            }
            break;
          case "raw_dump":
            setRawPackets(payload.packets || []);
            break;
          case "final":
            setGeminiReport(payload.gemini_report || null);
            break;
          default:
            console.warn("Unknown message type", payload);
        }
      },
      onStatusChange: setConnectionStatus,
    });
    return disconnect;
  }, []);

  return (
    <div className="app-shell">
      <Dashboard
        liveVitals={liveVitals}
        rawPackets={rawPackets}
        geminiReport={geminiReport}
        connectionStatus={connectionStatus}
      />
    </div>
  );
};

export default App;
