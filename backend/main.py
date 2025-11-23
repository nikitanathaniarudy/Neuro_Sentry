"""FastAPI backend: receives Presage packets, buffers session, and returns Gemini triage."""

from __future__ import annotations

import asyncio
import json
import sys
import os
import wave
import tempfile
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Dict, List, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from gemini_dummy import call_gemini_report
from schemas import PresagePacket

app = FastAPI(title="Neuro-Sentry Backend", version="0.7.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Shared State ---
state_lock = asyncio.Lock()
live_clients: List[WebSocket] = []
session_buffer: List[PresagePacket] = []
audio_buffer: bytearray = bytearray()
session_active: bool = False
last_raw_dump: List[Dict[str, Any]] | None = None
last_final_report: Dict[str, Any] | None = None


# --- Helpers ---

def _compute_stats(packets: List[PresagePacket]) -> Dict[str, Any]:
    """Basic stats: mean HR/BR/quality + simple facial asymmetry if points exist."""
    if not packets:
        return {"count": 0, "heart_rate_mean": None, "breathing_rate_mean": None, "quality_mean": None, "duration_ms": 0}

    hr_values = [p.heart_rate for p in packets if p.heart_rate is not None]
    br_values = [p.breathing_rate for p in packets if p.breathing_rate is not None]
    quality_values = [p.quality for p in packets if p.quality is not None]

    NOSE_TIP, MOUTH_LEFT, MOUTH_RIGHT, BROW_LEFT, BROW_RIGHT = 1, 61, 291, 105, 334
    mouth_asym, brow_asym = [], []
    for p in packets:
        pts = p.face_points
        if len(pts) > max(BROW_RIGHT, MOUTH_RIGHT):
            try:
                nose_y = pts[NOSE_TIP][1]
                mouth_asym.append(abs(abs(pts[MOUTH_LEFT][1] - nose_y) - abs(pts[MOUTH_RIGHT][1] - nose_y)) * 100)
                brow_asym.append(abs(abs(pts[BROW_LEFT][1] - nose_y) - abs(pts[BROW_RIGHT][1] - nose_y)) * 100)
            except Exception:
                continue

    def safe_mean(vals):
        return mean(vals) if vals else None

    return {
        "count": len(packets),
        "heart_rate_mean": safe_mean(hr_values),
        "breathing_rate_mean": safe_mean(br_values),
        "quality_mean": safe_mean(quality_values),
        "mouth_asymmetry_mean": safe_mean(mouth_asym),
        "brow_asymmetry_mean": safe_mean(brow_asym),
        "duration_ms": (packets[-1].timestamp - packets[0].timestamp).total_seconds() * 1000 if packets else 0,
    }


async def broadcast_to_live_clients(payload: Dict[str, Any]) -> None:
    """Send JSON payload to all connected live_state clients."""
    stale: List[WebSocket] = []
    client_count = len(live_clients)
    print(f"[broadcast] type={payload.get('type')} -> {client_count} clients")
    for client in list(live_clients):
        try:
            await client.send_json(payload)
        except (WebSocketDisconnect, RuntimeError):
            stale.append(client)

    if stale:
        async with state_lock:
            for client in stale:
                if client in live_clients:
                    live_clients.remove(client)


# --- WebSocket Endpoints ---

@app.websocket("/presage_stream")
async def presage_stream(websocket: WebSocket) -> None:
    """iOS bridge pushes Presage control + vitals packets + audio bytes here."""
    await websocket.accept()
    print("[presage_stream] iOS client connected.")

    global session_active, session_buffer, audio_buffer, last_raw_dump, last_final_report

    try:
        while True:
            # Handle both text (JSON) and binary (Audio) messages
            message = await websocket.receive()
            
            if message["type"] == "websocket.disconnect":
                print("[presage_stream] Received disconnect message")
                break

            if "bytes" in message and message["bytes"]:
                # Audio Chunk
                # print(f"[presage_stream] Received audio chunk: {len(message['bytes'])} bytes") # Optional: verbose logging
                async with state_lock:
                    if session_active:
                        audio_buffer.extend(message["bytes"])
                continue

            if "text" in message and message["text"]:
                raw = json.loads(message["text"])
                msg_type = raw.get("type")
                print(f"[presage_stream] received msg_type={msg_type}")

                if msg_type == "session_start":
                    async with state_lock:
                        session_buffer = []
                        audio_buffer = bytearray()
                        session_active = True
                        last_raw_dump = None
                        last_final_report = None
                    print("[presage_stream] session_start")

                elif msg_type == "vitals":
                    async with state_lock:
                        if not session_active:
                            continue
                    try:
                        packet = PresagePacket.model_validate(raw)
                    except Exception as exc:
                        print(f"[presage_stream] Packet validation failed: {exc}; keys={list(raw.keys())}")
                        continue

                    async with state_lock:
                        session_buffer.append(packet)
                        live_summary = {
                            "heart_rate": packet.heart_rate,
                            "breathing_rate": packet.breathing_rate,
                            "quality": packet.quality,
                            "blood_pressure": packet.blood_pressure,
                            "face_points": packet.face_points,
                            "session_packet_count": len(session_buffer),
                        }
                    await broadcast_to_live_clients({"type": "live", "data": live_summary})

                elif msg_type == "session_end":
                    async with state_lock:
                        buffer_copy = list(session_buffer)
                        audio_copy = bytes(audio_buffer)
                        session_buffer = []
                        audio_buffer = bytearray()
                        session_active = False

                    stats = _compute_stats(buffer_copy)
                    dump_data = [p.model_dump(mode="json") for p in buffer_copy]
                    
                    # Save audio to temp file
                    temp_wav_path = None
                    if audio_copy:
                        try:
                            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                                temp_wav_path = tmp.name
                                with wave.open(tmp, "wb") as wf:
                                    wf.setnchannels(1)
                                    wf.setsampwidth(2) # 16-bit PCM
                                    wf.setframerate(16000) # Assuming 16kHz from iOS
                                    wf.writeframes(audio_copy)
                            print(f"[Audio] Saved {len(audio_copy)} bytes to {temp_wav_path}")
                        except Exception as e:
                            print(f"[Audio] Error saving WAV: {e}")

                    # Call Gemini with Audio
                    gemini_report = await call_gemini_report(stats, dump_data, audio_path=temp_wav_path)
                    
                    # Cleanup temp file
                    if temp_wav_path and os.path.exists(temp_wav_path):
                        os.remove(temp_wav_path)

                    async with state_lock:
                        last_raw_dump = dump_data
                        last_final_report = gemini_report

                    await broadcast_to_live_clients({"type": "raw_dump", "packets": dump_data})
                    await broadcast_to_live_clients({"type": "final", "gemini_report": gemini_report})
                    print("[presage_stream] session_end -> final report broadcast")

    except WebSocketDisconnect:
        print("[presage_stream] iOS client disconnected.")
    except Exception as exc:
        print(f"[presage_stream] Error: {exc}")


@app.websocket("/live_state")
async def live_state(websocket: WebSocket) -> None:
    """Frontend clients subscribe here for live and final messages."""
    await websocket.accept()
    async with state_lock:
        live_clients.append(websocket)
        print(f"[live_state] Web client connected. Total: {len(live_clients)}")
        if last_raw_dump is not None:
            await websocket.send_json({"type": "raw_dump", "packets": last_raw_dump})
        if last_final_report is not None:
            await websocket.send_json({"type": "final", "gemini_report": last_final_report})

    try:
        while True:
            await asyncio.sleep(60)  # keep alive
    except WebSocketDisconnect:
        print("[live_state] Web client disconnected.")
    finally:
        async with state_lock:
            if websocket in live_clients:
                live_clients.remove(websocket)
        print(f"[live_state] Cleaned up client. Total: {len(live_clients)}")
