"""FastAPI backend for Neuro-Sentry demo with session + final Gemini report."""

from __future__ import annotations

import asyncio
import json
import sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque, Dict, List, Any, Tuple

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from gemini_dummy import call_gemini_report
from schemas import PresagePacket

app = FastAPI(title="Neuro-Sentry Backend", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared State
state_lock = asyncio.Lock()
live_clients: List[WebSocket] = []
session_buffer: Deque[PresagePacket] = deque()
session_active: bool = False
# State for final report sequence
raw_dump_to_send: List[Dict] | None = None
final_report_to_send: Dict | None = None

# --- Helper Functions ---

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _compute_stats(packets: List[PresagePacket]) -> Dict[str, object]:
    if not packets:
        return {}
    hr = [p.heart_rate for p in packets if p.heart_rate is not None]
    br = [p.breathing_rate for p in packets if p.breathing_rate is not None]
    quality = [p.quality for p in packets if p.quality is not None]
    return {
        "count": len(packets),
        "heart_rate_mean": sum(hr) / len(hr) if hr else 0.0,
        "breathing_rate_mean": sum(br) / len(br) if br else 0.0,
        "quality_mean": sum(quality) / len(quality) if quality else 0.0,
        "duration_ms": (packets[-1].timestamp - packets[0].timestamp).total_seconds() * 1000,
    }

async def broadcast_to_live_clients(payload: Dict):
    disconnected_clients = []
    for client in live_clients:
        try:
            await client.send_json(payload)
        except (WebSocketDisconnect, RuntimeError):
            disconnected_clients.append(client)
    for client in disconnected_clients:
        live_clients.remove(client)

# --- WebSocket Endpoints ---

@app.websocket("/presage_stream")
async def presage_stream(websocket: WebSocket) -> None:
    """Receive Presage packets and maintain a rolling in-memory buffer."""
    await websocket.accept()
    global session_active, raw_dump_to_send, final_report_to_send

    try:
        while True:
            message = await websocket.receive_text()
            try:
                raw = json.loads(message)
            except json.JSONDecodeError:
                continue

            msg_type = raw.get("type")
            
            async with state_lock:
                if msg_type == "session_start":
                    print("[presage_stream] session_start received")
                    session_buffer.clear()
                    session_active = True
                    raw_dump_to_send = None
                    final_report_to_send = None

                elif msg_type == "session_end":
                    print("[presage_stream] session_end received")
                    if session_active and session_buffer:
                        # 1. Freeze buffer and prepare raw dump
                        dump = [p.model_dump() for p in session_buffer]
                        raw_dump_to_send = dump
                        
                        # 2. Compute stats and run Gemini triage
                        stats = _compute_stats(list(session_buffer))
                        gemini_report = await call_gemini_report(stats, dump)
                        final_report_to_send = gemini_report
                    
                    session_active = False
                    session_buffer.clear()

                elif msg_type == "vitals" and session_active:
                    try:
                        packet = PresagePacket.model_validate(raw)
                        session_buffer.append(packet)
                        
                        # Create and broadcast live summary
                        live_summary = {
                            "heart_rate": packet.heart_rate,
                            "breathing_rate": packet.breathing_rate,
                            "quality": packet.quality,
                            "session_packet_count": len(session_buffer),
                        }
                        await broadcast_to_live_clients({"type": "live", "data": live_summary})
                    except Exception as e:
                        print(f"[presage_stream] Error validating vitals packet: {e}")
                
    except WebSocketDisconnect:
        print("[presage_stream] Client disconnected.")
    except Exception as e:
        print(f"[presage_stream] Error: {e}")

@app.websocket("/live_state")
async def live_state(websocket: WebSocket) -> None:
    """Stream the latest summaries and triage/final output to the browser."""
    await websocket.accept()
    live_clients.append(websocket)
    
    global raw_dump_to_send, final_report_to_send

    try:
        # On connect, send any pending final reports
        async with state_lock:
            if raw_dump_to_send:
                await websocket.send_json({"type": "raw_dump", "packets": raw_dump_to_send})
            if final_report_to_send:
                await websocket.send_json({"type": "final", "gemini_report": final_report_to_send})

        while True:
            # This loop now primarily handles broadcasting initiated from /presage_stream
            # and periodically sending new final reports to late-joining clients.
            async with state_lock:
                if raw_dump_to_send:
                    await broadcast_to_live_clients({"type": "raw_dump", "packets": raw_dump_to_send})
                    raw_dump_to_send = None # Clear after sending
                if final_report_to_send:
                    await broadcast_to_live_clients({"type": "final", "gemini_report": final_report_to_send})
                    final_report_to_send = None # Clear after sending
            
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        print("[live_state] Client disconnected.")
    finally:
        if websocket in live_clients:
            live_clients.remove(websocket)

# --- HTTP Endpoints ---

@app.get("/health")
async def health() -> Dict[str, object]:
    return {
        "ok": True,
        "live_clients": len(live_clients),
        "session_active": session_active,
        "session_buffer_size": len(session_buffer),
    }

@app.get("/")
async def root_health() -> Dict[str, object]:
    return await health()
