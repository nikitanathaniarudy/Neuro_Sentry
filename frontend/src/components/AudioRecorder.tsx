import React, { useEffect, useRef, useState } from "react";

type AudioRecorderProps = {
  startToken: number;
  label: string;
  onUploaded?: (ok: boolean) => void;
};

export const AudioRecorder: React.FC<AudioRecorderProps> = ({ startToken, label, onUploaded }) => {
  const [status, setStatus] = useState<"idle" | "recording" | "uploading" | "error">("idle");
  const [supported, setSupported] = useState<boolean>(true);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  useEffect(() => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setSupported(false);
      return;
    }

    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        const recorder = new MediaRecorder(stream);
        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) chunksRef.current.push(e.data);
        };
        recorder.onstop = async () => {
          const blob = new Blob(chunksRef.current, { type: "audio/wav" });
          chunksRef.current = [];
          setStatus("uploading");
          try {
            const resp = await fetch(
              `http://localhost:8000/audio?label=${encodeURIComponent(label)}`,
              { method: "POST", body: blob, headers: { "Content-Type": "audio/wav" } }
            );
            onUploaded?.(resp.ok);
            setStatus(resp.ok ? "idle" : "error");
          } catch (err) {
            console.error("upload failed", err);
            setStatus("error");
            onUploaded?.(false);
          }
        };
        recorderRef.current = recorder;
      })
      .catch(() => setSupported(false));
  }, [label, onUploaded]);

  const triggerRecording = () => {
    if (!recorderRef.current) return;
    if (status === "recording") return;
    chunksRef.current = [];
    recorderRef.current.start();
    setStatus("recording");
    window.setTimeout(() => recorderRef.current?.stop(), 4000);
  };

  useEffect(() => {
    if (startToken > 0) {
      triggerRecording();
    }
  }, [startToken]);

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0 }}>Audio Recorder</h3>
        <span className="status-chip">{supported ? status : "mic unsupported"}</span>
      </div>
      <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
        <button className="primary" onClick={triggerRecording} disabled={!supported || status === "recording"}>
          {status === "recording" ? "Recording..." : "Record now"}
        </button>
        <div style={{ fontSize: 12, opacity: 0.8 }}>Label: {label}</div>
      </div>
    </div>
  );
};

export default AudioRecorder;
