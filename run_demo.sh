#!/usr/bin/env bash
set -euo pipefail

# Local demo helper: start backend and frontend (no ngrok/tunnels).

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

function cleanup() {
  echo "\n[run_demo] shutting down..."
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT

echo "[run_demo] starting backend on 0.0.0.0:8000"
cd "$BACKEND_DIR"
python -m pip install -r requirements.txt >/dev/null 2>&1 || true
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 2

echo "[run_demo] curling health check: http://localhost:8000/health"
curl -s "http://localhost:8000/health" || true

cd "$FRONTEND_DIR"
echo "[run_demo] starting frontend on 0.0.0.0:5173"
npm install >/dev/null 2>&1 || true
npm run dev -- --host 0.0.0.0 --port 5173 >/dev/null 2>&1 &
FRONTEND_PID=$!

cat <<EOF

============================================================
 NEURO-SENTRY LOCAL DEMO
------------------------------------------------------------
 Backend health: http://localhost:8000/health
 Presage WS (iPhone): ws://<YOUR_MAC_LAN_IP>:8000/presage_stream
 Frontend WS:        ws://localhost:8000/live_state
 Frontend:           http://localhost:5173
============================================================
Ctrl+C to stop everything.
EOF

wait
