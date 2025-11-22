# Neuro-Sentry — Codex AGENTS.md

You are Codex CLI operating inside a 36-hour hackathon repo. 
Always follow the architecture, scope limits, and coding rules below.
Codex reads this file before doing any work. :contentReference[oaicite:2]{index=2}

---

## 0) Mission (what to build)
Ship a **webpage demo** for Neuro-Sentry using:
- **Presage-only sensing** (face + vitals) via a **native bridge** app.
- **FastAPI backend** that receives Presage packets + browser audio.
- **Gemini API** as the **dummy model** returning structured triage JSON.
- **No database, no auth, no sessions**. Everything is live in RAM.

The output must reliably drive a 30-second demo:
- face region highlights
- vitals trace
- triage score (1–5) + rationale
- red alert animation when high risk

---

## 1) Non-negotiable scope limits
1. **Webpage only.** No native UI app. The native bridge has no UI beyond “running.”
2. **Presage only for face & vitals.** Do not add MediaPipe or other landmark stacks.
3. **No database.** No session IDs, no users, no persistence.
4. **No deep-model training.** Use deterministic placeholders; Gemini is the temporary triage brain.
5. **Demo stability > ambition.** Avoid features that risk integration.

If a requested change violates scope, say so and propose a minimal in-scope alternative.

---

## 2) Architecture (end-to-end)
### Data sources
- **Native Presage Bridge** (C++ desktop preferred, or Android/iOS):
  - Opens webcam.
  - Runs Presage SmartSpectra.
  - Emits live packets:
    - face points / facial regions
    - heart rate, breathing rate
    - confidence / quality

> Note: Presage does not run in browser; the bridge is mandatory. (Reference only; do not redesign.) 

- **Browser Webpage**:
  - Displays dashboard and prompts.
  - Records audio clips (3–5 sec) for speech tasks.
  - Sends audio to backend.

### Transport
- Bridge → backend:
  - **WS `/presage_stream`**
  - one connection, push JSON ~2–5 Hz

- Webpage ↔ backend:
  - **WS `/live_state`** (backend → frontend, continuous)
  - **POST `/audio`** (frontend → backend, per prompt)

### Backend processing
- Keep **rolling buffers in RAM** only.
- Compute quick deterministic features.
- Call Gemini dummy model with:
  - Presage window summary
  - audio feature summary
- Gemini returns **strict JSON** matching `TriageOutput` schema.

### Frontend rendering
- Connect to `/live_state`.
- Render:
  - Presage mesh/regions
  - vitals numbers + traces
  - audio feature graph
  - triage panel + alert overlay
- Drive prompt script:
  - neutral → smile → eyebrows → phrase

---

## 3) Target repo structure
Create/maintain this layout:

neuro_sentry/
  AGENTS.md
  GEMINI.md
  backend/
    main.py
    gemini_dummy.py
    schemas.py
    features.py
    requirements.txt
    .env.example
  frontend/
    package.json
    vite.config.(ts|js)
    src/
      main.tsx
      App.tsx
      ws.ts
      components/
        Dashboard.tsx
        PromptPanel.tsx
        AudioRecorder.tsx
        MeshView.tsx
  bridge/
    README.md
    (native Presage code lives here but Codex may not modify unless asked)

Do not introduce extra top-level folders unless required.

---

## 4) Backend build rules (FastAPI)
### Required endpoints
1. **WS `/presage_stream`**
   - validate incoming Presage packet
   - append to rolling in-memory window (last ~2–3 seconds)
   - store `latest_presage_summary`

2. **POST `/audio`**
   - accept WAV/PCM bytes + label
   - extract lightweight features (MFCC stats, jitter/shimmer proxy)
   - store `latest_audio_summary`

3. **WS `/live_state`**
   - every 200–500 ms:
     - call `call_gemini_dummy(latest_presage_summary, latest_audio_summary)`
     - send `{presage_summary, audio_summary, triage_output}`

### Schemas
In `schemas.py`, define pydantic models:
- `PresagePacket`
- `AudioPacket`
- `TriageOutput`

`TriageOutput` must include:
- `overall_risk: float (0..1)`
- `triage_level: int (1..5)`
- `confidence: float (0..1)`
- `rationale_short: str`
- `ui_directives: { alert_color, highlight_regions[] }`

### Gemini dummy model file
In `gemini_dummy.py`:
- use Google GenAI SDK client (reads `GEMINI_API_KEY` env). :contentReference[oaicite:3]{index=3}
- enforce structured JSON output (see GEMINI.md prompt/schema).

### No persistence
Do not add DB, caching layers, or session storage.

---

## 5) Frontend build rules (Vite React TS)
### Required modules
- `ws.ts`: WS client for `/live_state`.
- `PromptPanel.tsx`: prompt script with timers.
- `AudioRecorder.tsx`: records + POSTs to `/audio`.
- `MeshView.tsx`: render Presage face points/regions.
- `Dashboard.tsx`: layout + graphs + alert overlay.

### UX rules
- Show clear “data connected / not connected.”
- “Red alert” animation must be dramatic but stable.
- If WS disconnects, UI falls back to last known state.

---

## 6) Coding standards
- Python 3.11+
- Type hints everywhere new.
- Keep functions small and obvious.
- Avoid clever refactors unless asked.
- Prefer readability over micro-optimization.
- Add minimal comments for signal meaning.

---

## 7) Dev commands to preserve
Backend:
- `cd backend`
- `python -m pip install -r requirements.txt`
- `uvicorn main:app --reload --port 8000`

Frontend:
- `cd frontend`
- `npm install`
- `npm run dev`

---

## 8) How Codex should operate here
- **Primary role:** make code changes, scaffold files, wire endpoints, fix bugs.
- **Never hallucinate APIs**; if unsure, leave TODO + minimal safe default.
- **Follow the repo structure above.**
- Provide changes as clear diffs or file outputs.
- Do not add MCP servers unless user explicitly asks. MCP is optional. :contentReference[oaicite:4]{index=4}
- Remember Codex local agent runs with network disabled by default; don’t rely on live web lookups. :contentReference[oaicite:5]{index=5}

---

## 9) Definition of done
A fresh clone can run:
- backend + frontend with one command each
- simulated Presage packets (if bridge absent) still show triage changing
- Gemini dummy output is always valid JSON
- 30-second demo works 3 times in a row
