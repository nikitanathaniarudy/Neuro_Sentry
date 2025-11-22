#!/usr/bin/env bash
set -euo pipefail

# Demo helper: start backend, ngrok, and frontend with clear URLs for iOS bridge.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

function cleanup() {
  echo "\n[run_demo] shutting down..."
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ -n "${NGROK_PID:-}" ]] && kill "$NGROK_PID" 2>/dev/null || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT

if ! command -v ngrok >/dev/null 2>&1; then
  echo "[run_demo] ngrok not found. Install from https://ngrok.com/download and ensure it's on PATH." >&2
  exit 1
fi

echo "[run_demo] starting backend on 0.0.0.0:8000"
cd "$BACKEND_DIR"
python -m pip install -r requirements.txt >/dev/null 2>&1 || true
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 2

echo "[run_demo] starting ngrok tunnel to 8000"
NGROK_LOG="$(mktemp)"
ngrok http 8000 --log=stdout >"$NGROK_LOG" 2>&1 &
NGROK_PID=$!

# Wait for ngrok URL
NGROK_URL=""
for i in {1..20}; do
  if grep -q "msg=\"started tunnel\"" "$NGROK_LOG"; then
    NGROK_URL=$(grep -m1 -oE "https://[a-zA-Z0-9.-]+\\.ngrok-free\\.(app|dev)" "$NGROK_LOG" || true)
    [[ -z "$NGROK_URL" ]] && NGROK_URL=$(grep -m1 -oE "https://[a-zA-Z0-9.-]+\\.ngrok\\.io" "$NGROK_LOG" || true)
    if [[ -n "$NGROK_URL" ]]; then
      break
    fi
  fi
  sleep 1
done

if [[ -z "$NGROK_URL" ]]; then
  echo "[run_demo] failed to detect ngrok URL; check $NGROK_LOG" >&2
  cleanup
  exit 1
fi

WSS_URL="${NGROK_URL/https:/wss:}/presage_stream"

echo "[run_demo] curling health check: $NGROK_URL/health"
curl -s "$NGROK_URL/health" || true

cd "$FRONTEND_DIR"
echo "[run_demo] starting frontend on 0.0.0.0:5173"
npm install >/dev/null 2>&1 || true
npm run dev -- --host 0.0.0.0 --port 5173 >/dev/null 2>&1 &
FRONTEND_PID=$!

cat <<EOF

============================================================
 NEURO-SENTRY DEMO TUNNEL
------------------------------------------------------------
 Health URL:   $NGROK_URL/health
 WSS (Swift):  $WSS_URL
 Frontend:     http://localhost:5173
============================================================
Ctrl+C to stop everything.
EOF

wait
