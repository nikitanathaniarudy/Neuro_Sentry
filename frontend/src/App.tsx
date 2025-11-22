import React, { useEffect, useState } from "react";
import Dashboard from "./components/Dashboard";
import { LiveStateMessage, connectLiveState } from "./ws";

const App: React.FC = () => {
  const [liveData, setLiveData] = useState<Record<string, any> | null>(null);
  const [rawPackets, setRawPackets] = useState<Record<string, unknown>[]>([]);
  const [finalReport, setFinalReport] = useState<Record<string, unknown> | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<"connecting" | "open" | "closed">("connecting");

  useEffect(() => {
    const disconnect = connectLiveState({
      onMessage: (payload) => {
        switch (payload.type) {
          case "live":
            setLiveData(payload.data || null);
            break;
          case "raw_dump":
            setRawPackets(payload.packets || []);
            setFinalReport(null); // Clear previous final report
            setLiveData(null); // Clear live data on new session
            break;
          case "final":
            setFinalReport(payload.gemini_report || {});
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
        liveData={liveData}
        rawPackets={rawPackets}
        connectionStatus={connectionStatus}
        finalReport={finalReport}
      />
    </div>
  );
};

export default App;
