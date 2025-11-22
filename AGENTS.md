# Neuro-Sentry — Codex AGENTS.md (Hackathon)

You are Codex CLI operating inside a 36-hour hackathon repo.
Follow this file literally. Optimize for a stable demo, not elegance.

---

## 0) Mission (what to ship)
Ship a **web landing-page demo** showing Neuro-Sentry end-to-end:

- **Presage-only sensing** (face + vitals) from a **native iOS bridge**.
- **FastAPI backend** that ingests Presage packets + browser audio.
- **Gemini API** as the temporary triage/model brain returning strict JSON.
- **No database / no auth / no sessions**. Live RAM only.

Demo must show, in real time:
- vitals (HR/BR)
- face mesh / region states
- audio features
- triage risk score + rationale
- red alert overlay when high risk

---

## 1) Non-negotiable scope limits
1. **Webpage is the product.** iOS bridge has no UI besides Presage camera view.
2. **Presage only for face & vitals.** No MediaPipe, no extra landmark stacks.
3. **No persistence.** No DB, no sessions, no user storage.
4. **No training required.** Gemini + deterministic proxies only for demo.
5. **Stability > ambition.** Prefer safe minimal code.

If a request violates scope, say so and propose an in-scope alternative.

---

## 2) Current reality / constraints to handle
- iOS Presage works and prints vitals in Xcode console.
- Phone **cannot reliably open http://<mac-ip>:8000/docs** over Wi-Fi yet.
- Therefore Codex must:
  1) add backend debug/health endpoints + logs to prove packet arrival,
  2) ensure backend WS accepts LAN connections,
  3) keep demo alive even if iOS WS is unreachable (simulate Presage),
  4) make frontend clearly show connection state + timestamps.

Do not require the judge to be on the same LAN for the demo to work.

---

## 3) Architecture (end-to-end)
### Sources
**iOS Presage Bridge**
- Runs SmartSpectra continuous mode.
- Streams JSON packets 2–5 Hz to backend WS `/presage_stream`.

**Browser Webpage**
- Connects to backend WS `/live_state`.
- Records short audio on prompt → POST `/audio`.

### Transport
- Bridge → backend: WS `/presage_stream`
- Frontend ↔ backend: WS `/live_state` and POST `/audio`

### Backend processing
- Rolling RAM window only (~2–3s Presage, last audio clip).
- Compute deterministic summaries.
- Call Gemini with strict JSON schema (GEMINI.md).
- Output `TriageOutput` regardless of missing data.

### Frontend rendering
- Show connected/disconnected states.
- Render mesh points if present.
- Show vitals + audio features.
- Show triage + dramatic red alert overlay.
- Prompt script: neutral → smile → eyebrows → phrase → record audio.

---

## 4) Backend build rules (FastAPI)
### Required endpoints
1. **WS `/presage_stream`**
   - validate packet
   - append to rolling buffer
   - update `latest_presage_summary`
   - **log packet_count + last_timestamp**

2. **POST `/audio`**
   - accept WAV/PCM + label
   - extract light features (MFCC stats, jitter/shimmer proxy)
   - update `latest_audio_summary`
   - **log label + feature summary**

3. **WS `/live_state`**
   - every 200–500ms:
     - compute presage_summary + audio_summary
     - call Gemini dummy → triage_output
     - send `{presage_summary, audio_summary, triage_output, debug}`

### NEW required debug endpoints (Codex must add)
4. **GET `/health`**
   - returns `{ok: true, presage_packets_seen, last_presage_ts, last_audio_ts}`

5. **GET `/debug_state`**
   - returns the latest RAM summaries + counts (safe, no secrets)

### Networking must-haves
- Bind host `0.0.0.0`.
- Add CORS allow-all for hackathon.
- WS must not require auth.

### Schemas
In `schemas.py` the pydantic models:
- `PresagePacket`
- `AudioPacket`
- `TriageOutput`

`TriageOutput` fields:
- `overall_risk: float (0..1)`
- `triage_level: int (1..5)`
- `confidence: float (0..1)`
- `rationale_short: str`
- `ui_directives: { alert_color, highlight_regions[] }`

---

## 5) Frontend build rules (Vite React TS)
### Required modules
- `ws.ts` client for `/live_state`.
- `Dashboard.tsx`, `PromptPanel.tsx`, `AudioRecorder.tsx`, `MeshView.tsx`.

### NEW required UX/debug
- Show a top-right “**LIVE / DISCONNECTED**” indicator.
- Show “last presage packet age” and “last audio age”.
- If presage missing, clearly say “using simulated vitals”.

---

## 6) Simulation fallback (must exist)
If `/presage_stream` has seen 0 packets for >3 seconds,
backend must synthesize a fake Presage window so demo still runs.

Simulation must be obvious in debug fields.

---

## 7) Dev commands (preserve)
Backend:
- `cd backend`
- `python -m pip install -r requirements.txt`
- `uvicorn main:app --reload --host 0.0.0.0 --port 8000`

Frontend:
- `cd frontend`
- `npm install`
- `npm run dev`

---

## 8) Codex operating rules
- Make changes as diffs / full files.
- Do not hallucinate APIs.
- Do not touch bridge/ios unless explicitly asked.
- Keep code readable and tiny.

---

## 9) Definition of done
A fresh clone can run:
- backend + frontend with one command each
- demo works **with real iOS Presage OR simulated packets**
- `/health` shows packet counts live
- `/live_state` always sends valid JSON
- 30-second demo works 3 times in a row
