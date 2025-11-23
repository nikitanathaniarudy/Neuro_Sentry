# Neuro Sentry Project

## Local Run (backend)
1) `cd backend`
2) `python -m pip install -r requirements.txt`
3) Export `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in your shell for Gemini 2.0 Flash Lite. If not set, deterministic fallback is used.
4) `uvicorn main:app --reload --host 0.0.0.0 --port 8000`

## Local Run (frontend)
1) `cd frontend`
2) `npm install`
3) Optionally set `VITE_BACKEND_WS=ws://<mac-ip>:8000/live_state` in `.env` (defaults to localhost).
4) `npm run dev`

## iOS App
- Open `bridge/ios/NeuroSentryBridge` in Xcode on your Mac.
- In `PresageBridgeClient.swift`, set `BACKEND_WS` to `ws://<mac-ip>:8000/presage_stream`.
- In `ContentView.swift`, paste your Presage API key.
- Build/run on your iPhone. Press “End Session” to stop and trigger the Gemini report.
