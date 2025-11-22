"""FastAPI backend for Neuro-Sentry demo."""

from __future__ import annotations

import asyncio
import sys
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Deque, Dict, Tuple

from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.websockets import WebSocketState

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from features import compute_audio_features, summarize_presage_window, trim_presage_window
from gemini_dummy import call_gemini_dummy
from schemas import AudioPacket, PresagePacket


app = FastAPI(title="Neuro-Sentry Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


presage_buffer: Deque[Tuple[datetime, PresagePacket]] = deque()
latest_presage_summary: Dict[str, object] = {}
latest_audio_summary: Dict[str, object] = {}
_latest_presage_is_simulated: bool = False # Track if the latest presage data is simulated
state_lock = asyncio.Lock()


@app.websocket("/presage_stream")
async def presage_stream(websocket: WebSocket) -> None:
    """Receive Presage packets and maintain a rolling in-memory buffer."""
    print("Backend: Entering presage_stream function.")
    await websocket.accept()
    print("Backend: WebSocket connection accepted.")
    global latest_presage_summary, _latest_presage_is_simulated
    try:
        while True:
            message = await websocket.receive_text()
            try:
                packet = PresagePacket.model_validate_json(message)
            except Exception as e:
                await websocket.send_json({"error": "invalid_packet", "details": str(e)})
                continue

            async with state_lock:
                presage_buffer.append((packet.timestamp, packet))
                trim_presage_window(presage_buffer)
                latest_presage_summary = summarize_presage_window(presage_buffer)
                _latest_presage_is_simulated = packet.is_simulated # Update simulation status

            await websocket.send_json({"status": "ok", "count": len(presage_buffer)})
    except WebSocketDisconnect:
        return
    except Exception:
        if websocket.application_state == WebSocketState.CONNECTED:
            await websocket.close(code=1011, reason="internal error")


@app.post("/audio")
async def ingest_audio(request: Request, label: str = Query("phrase")) -> JSONResponse:
    """Accept raw wav/PCM bytes, compute features, and store the latest summary."""

    global latest_audio_summary
    body = await request.body()
    audio_packet: AudioPacket = compute_audio_features(body, label=label)
    async with state_lock:
        latest_audio_summary = audio_packet.model_dump()

    return JSONResponse(content=audio_packet.model_dump())


@app.websocket("/live_state")
async def live_state(websocket: WebSocket) -> None:
    """Stream the latest summaries and triage output to the browser."""

    await websocket.accept()
    try:
        while True:
            async with state_lock:
                presage_snapshot = dict(latest_presage_summary)
                audio_snapshot = dict(latest_audio_summary)
                current_is_simulated = _latest_presage_is_simulated # Get current simulation status

            triage_output = await call_gemini_dummy(presage_snapshot, audio_snapshot)
            payload = {
                "presage_summary": presage_snapshot,
                "audio_summary": audio_snapshot,
                "triage_output": triage_output,
                "is_simulated": current_is_simulated, # Include simulation status
            }
            await websocket.send_json(payload)
            await asyncio.sleep(0.3)
    except WebSocketDisconnect:
        return
    except Exception:
        if websocket.application_state == WebSocketState.CONNECTED:
            await websocket.close(code=1011, reason="internal error")


@app.get("/")
async def health() -> Dict[str, str]:
    return {"status": "ok", "presage_buffer": str(len(presage_buffer))}
