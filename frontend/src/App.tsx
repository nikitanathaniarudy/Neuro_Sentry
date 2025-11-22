import React, { useEffect, useState } from "react";
import Dashboard from "./components/Dashboard";
import PromptPanel from "./components/PromptPanel";
import AudioRecorder from "./components/AudioRecorder";
import { LiveStateMessage, connectLiveState } from "./ws";

const defaultState: LiveStateMessage = {
  type: "live",
  presage_summary: {},
  audio_summary: {},
  triage_output: {
    overall_risk: 0,
    triage_level: 1,
    confidence: 0.5,
    rationale_short: "Waiting for signals...",
    ui_directives: { alert_color: "#43a047", highlight_regions: [] },
  },
  debug: { packet_age_ms: null as any, using_simulated_presage: false, last_audio_age_ms: null as any },
};

const App: React.FC = () => {
  const [liveState, setLiveState] = useState<LiveStateMessage>(defaultState);
  const [connectionStatus, setConnectionStatus] = useState<"connecting" | "open" | "closed">("connecting");
  const [recordToken, setRecordToken] = useState(0);
  const [recordLabel, setRecordLabel] = useState("phrase");
  const [finalReport, setFinalReport] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    const disconnect = connectLiveState({
      onMessage: (payload) => {
        if (payload.type === "final") {
          setFinalReport(payload.gemini_report || {});
        } else {
          setLiveState({
            ...payload,
            presage_summary: payload.presage_summary || {},
            audio_summary: payload.audio_summary || {},
            triage_output:
              payload.triage_output ||
              defaultState.triage_output,
          });
        }
      },
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
        debug={liveState.debug}
        finalReport={finalReport}
      />
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <PromptPanel onPhraseStart={handlePhraseStart} />
        <AudioRecorder startToken={recordToken} label={recordLabel} />
      </div>
    </div>
  );
};

export default App;
