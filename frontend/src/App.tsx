import React, { useEffect, useState } from "react";
import Dashboard from "./components/Dashboard";
import { GeminiReport, LiveStateMessage, LiveVitals, connectLiveState } from "./ws";

const App: React.FC = () => {
  const [liveVitals, setLiveVitals] = useState<LiveVitals | null>(null);
  const [rawPackets, setRawPackets] = useState<Record<string, unknown>[]>([]);
  const [geminiReport, setGeminiReport] = useState<GeminiReport | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<"connecting" | "open" | "closed">("connecting");
  const [recordingStatus, setRecordingStatus] = useState("Not recording");
  const [slurScore, setSlurScore] = useState<number | null>(null);

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
  // --- Audio recording handler ---
  const recordAudio = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const audioChunks: BlobPart[] = [];

      mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
      mediaRecorder.onstart = () => setRecordingStatus("Recording...");
      mediaRecorder.onstop = async () => {
        setRecordingStatus("Recording stopped");

        const blob = new Blob(audioChunks, { type: "audio/wav" });
        const formData = new FormData();
        formData.append("speech", blob);
        // Send audio to backend for slur detection
        const res = await fetch("http://localhost:8000/upload_speech", {
          method: "POST",
          body: formData,
        });
        const data = await res.json();
        setSlurScore(data.slur_score);
      };
       mediaRecorder.start();
      setTimeout(() => mediaRecorder.stop(), 4000); // record for 4 seconds
    } catch (err) {
      console.error("Audio recording failed", err);
      setRecordingStatus("Error accessing microphone");
    }
  };

  return (
    <div className="app-shell">
      <Dashboard
        liveVitals={liveVitals}
        rawPackets={rawPackets}
        geminiReport={geminiReport}
        connectionStatus={connectionStatus}
      />
      {/* --- Voice Recording UI --- */}
      <div style={{ marginTop: "20px", padding: "10px", borderTop: "1px solid #ccc" }}>
        <h3>Voice Slurring Detection</h3>
        <button onClick={recordAudio}>Record Phrase</button>
        <p>Status: {recordingStatus}</p>
        {slurScore !== null && <p>Slur Score: {slurScore}</p>}
      </div>
    </div>
  );
};

export default App;
