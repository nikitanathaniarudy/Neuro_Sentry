export type TriageOutput = {
  overall_risk: number;
  triage_level: number;
  confidence: number;
  rationale_short: string;
  ui_directives: { alert_color: string; highlight_regions: string[] };
};

export type LiveStateMessage = {
  type: "live" | "raw_dump" | "final";
  data?: Record<string, any>;
  packets?: Record<string, unknown>[];
  gemini_report?: Record<string, unknown>;
};

type Handlers = {
  onMessage: (payload: LiveStateMessage) => void;
  onStatusChange?: (status: "connecting" | "open" | "closed") => void;
};

export function connectLiveState({ onMessage, onStatusChange }: Handlers) {
  let socket: WebSocket | null = null;
  let reconnectTimer: number | undefined;

  const connect = () => {
    onStatusChange?.("connecting");
    const url = "ws://localhost:8000/live_state";
    socket = new WebSocket(url);

    socket.onopen = () => {
      onStatusChange?.("open");
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as LiveStateMessage;
        onMessage(data);
      } catch (err) {
        console.warn("Bad live_state message", err);
      }
    };

    socket.onclose = () => {
      onStatusChange?.("closed");
      reconnectTimer = window.setTimeout(connect, 1000);
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
