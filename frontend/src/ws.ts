export type LiveVitals = {
  heart_rate: number | null;
  breathing_rate: number | null;
  quality: number | null;
  blood_pressure?: { systolic: number; diastolic: number } | null;
  face_points?: number[][];
  session_packet_count: number;
};

export type GeminiReport = {
  risk_level: "LOW" | "MED" | "HIGH";
  stroke_probability: number;
  summary: string;
  recommendation: string;
  confidence: number;
  bell_palsy_probability?: number;
};

export type LiveStateMessage =
  | { type: "live"; data: LiveVitals }
  | { type: "raw_dump"; packets: Record<string, unknown>[] }
  | { type: "final"; gemini_report: GeminiReport };

type Handlers = {
  onMessage: (payload: LiveStateMessage) => void;
  onStatusChange?: (status: "connecting" | "open" | "closed") => void;
};

export function connectLiveState({ onMessage, onStatusChange }: Handlers) {
  let socket: WebSocket | null = null;
  let reconnectTimer: number | undefined;

  const connect = () => {
    onStatusChange?.("connecting");
    const url = (import.meta.env.VITE_BACKEND_WS as string) || "ws://172.20.10.2:8000/live_state";
    socket = new WebSocket(url);

    socket.onopen = () => {
      console.log("[live_state] ws open", url);
      onStatusChange?.("open");
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as LiveStateMessage;
        console.log("[live_state] message", (data as any).type);
        onMessage(data);
      } catch (err) {
        console.warn("Bad live_state message", err);
      }
    };

    socket.onclose = () => {
      console.log("[live_state] ws closed");
      onStatusChange?.("closed");
      reconnectTimer = window.setTimeout(connect, 1200);
    };

    socket.onerror = () => {
      socket?.close();
    };
  };

  connect();

  return () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
    }
    socket?.close();
  };
}
