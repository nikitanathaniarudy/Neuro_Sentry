import React, { useEffect, useState } from "react";
import Dashboard from "./components/Dashboard";
import PromptPanel from "./components/PromptPanel";
import AudioRecorder from "./components/AudioRecorder";
import { LiveStateMessage, connectLiveState } from "./ws";

const defaultState: LiveStateMessage = {
  presage_summary: {},
  audio_summary: {},
  triage_output: {
    overall_risk: 0,
    triage_level: 1,
    confidence: 0.5,
    rationale_short: "Waiting for signals...",
    ui_directives: { alert_color: "#43a047", highlight_regions: [] },
  },
  is_simulated: false, // Added default for new field
};

const App: React.FC = () => {
  const [liveState, setLiveState] = useState<LiveStateMessage>(defaultState);
  const [connectionStatus, setConnectionStatus] = useState<"connecting" | "open" | "closed">("connecting");
  const [recordToken, setRecordToken] = useState(0);
  const [recordLabel, setRecordLabel] = useState("phrase");

  useEffect(() => {
    const disconnect = connectLiveState({
      onMessage: (payload) => setLiveState(payload),
      onStatusChange: (status) => setConnectionStatus(status),
    });
    return disconnect;
  }, []);

  const handlePhraseStart = () => {
    setRecordLabel("phrase");
    setRecordToken((t) => t + 1);
  };

  return (
    <div className="app-shell">
      <Dashboard
        presageSummary={liveState.presage_summary}
        audioSummary={liveState.audio_summary}
        triageOutput={liveState.triage_output}
        connectionStatus={connectionStatus}
        isSimulated={liveState.is_simulated} // Pass the is_simulated prop
      />
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <PromptPanel onPhraseStart={handlePhraseStart} />
        <AudioRecorder startToken={recordToken} label={recordLabel} />
      </div>
    </div>
  );
};

export default App;
