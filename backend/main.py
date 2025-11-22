"""FastAPI backend for Neuro-Sentry demo with session + final Gemini report."""

from __future__ import annotations

import asyncio
import json
import sys
from collections import deque
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Deque, Dict, Tuple, Any

from fastapi import FastAPI, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.websockets import WebSocketState

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from features import (
    build_simulated_presage,
    compute_audio_features,
    summarize_presage_window,
    trim_presage_window,
)
from gemini_dummy import call_gemini_dummy, call_gemini_report
from schemas import AudioPacket, PresagePacket

app = FastAPI(title="Neuro-Sentry Backend", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


presage_buffer: Deque[Tuple[datetime, PresagePacket]] = deque()
session_buffer: Deque[Tuple[datetime, PresagePacket]] = deque(maxlen=300)
latest_presage_summary: Dict[str, object] = {}
latest_audio_summary: Dict[str, object] = {}
last_triage_output: Dict[str, object] = {}
last_gemini_report: Dict[str, object] = {}
session_active: bool = False
session_packets: int = 0
final_version: int = 0
last_final_version_sent: int = 0
presage_packets_seen: int = 0
last_presage_ts: datetime | None = None
last_audio_ts: datetime | None = None
presage_connected_clients: int = 0
live_state_clients: int = 0
state_lock = asyncio.Lock()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _age_ms(ts: datetime | None) -> int:
    if not ts:
        return 1_000_000
    return int((_now() - ts).total_seconds() * 1000)


def _ensure_presage_summary() -> tuple[Dict[str, object], bool]:
    global latest_presage_summary
    age_ms = _age_ms(last_presage_ts)
    if presage_packets_seen == 0 or age_ms > 3000:
        simulated = build_simulated_presage(_now())
        return simulated, True
    return dict(latest_presage_summary), False


def _finalize_session() -> Dict[str, object]:
    presage_snapshot, _ = _ensure_presage_summary()
    # Basic stats from session_buffer
    hr_vals = [p.heart_rate for _, p in session_buffer if p.heart_rate is not None]
    br_vals = [p.breathing_rate for _, p in session_buffer if p.breathing_rate is not None]
    quality_vals = [p.quality for _, p in session_buffer if p.quality is not None]
    presage_snapshot.update(
        {
            "session_count": len(session_buffer),
            "session_hr_mean": sum(hr_vals) / len(hr_vals) if hr_vals else 0.0,
            "session_br_mean": sum(br_vals) / len(br_vals) if br_vals else 0.0,
            "session_hr_min": min(hr_vals) if hr_vals else 0.0,
            "session_hr_max": max(hr_vals) if hr_vals else 0.0,
            "session_quality": sum(quality_vals) / len(quality_vals) if quality_vals else 0.0,
        }
    )
    return presage_snapshot


@app.websocket("/presage_stream")
async def presage_stream(websocket: WebSocket) -> None:
    """Receive Presage packets and maintain a rolling in-memory buffer."""

    await websocket.accept()
    global presage_connected_clients, session_active, session_packets, final_version
    presage_connected_clients += 1
    try:
        while True:
            message = await websocket.receive_text()
            try:
                raw = json.loads(message)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "invalid_json"})
                continue

            msg_type = raw.get("type", "vitals")
            ts_str = raw.get("timestamp")
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")) if ts_str else _now()
            except Exception:
                ts = _now()

            if msg_type == "session_start":
                async with state_lock:
                    session_buffer.clear()
                    session_active = True
                    session_packets = 0
                    final_version += 1  # bump to invalidate previous final
                print("[presage_stream] session_start received")
                await websocket.send_json({"status": "session_started"})
                continue

            if msg_type == "session_end":
                async with state_lock:
                    session_active = False
                    presage_snapshot = _finalize_session()
                gemini_report = await call_gemini_report(presage_snapshot, latest_audio_summary)
                async with state_lock:
                    last_gemini_report.update(gemini_report)
                    final_version += 1
                print("[presage_stream] session_end received, final report ready")
                await websocket.send_json({"status": "session_ended"})
                continue

            # treat as vitals packet
            try:
                packet = PresagePacket.model_validate(
                    {
                        "timestamp": ts,
                        "heart_rate": raw.get("heart_rate"),
                        "breathing_rate": raw.get("breathing_rate"),
                        "quality": raw.get("quality"),
                        "regions": raw.get("regions", {}),
                        "face_points": raw.get("face_points", []),
                    }
                )
            except Exception as exc:
                await websocket.send_json({"error": "invalid_packet", "details": str(exc)})
                continue

            async with state_lock:
                global presage_packets_seen, last_presage_ts, latest_presage_summary
                presage_packets_seen += 1
                last_presage_ts = packet.timestamp
                presage_buffer.append((packet.timestamp, packet))
                trim_presage_window(presage_buffer, window_seconds=60.0)
                latest_presage_summary = summarize_presage_window(presage_buffer, window_seconds=60.0)
                if session_active:
                    session_packets += 1
                    session_buffer.append((packet.timestamp, packet))

            print(
                f"[presage_stream] count={presage_packets_seen} hr={packet.heart_rate} br={packet.breathing_rate} quality={packet.quality}"
            )
            await websocket.send_json({"status": "ok", "count": len(presage_buffer)})
    except WebSocketDisconnect:
        pass
    except Exception:
        if websocket.application_state == WebSocketState.CONNECTED:
            await websocket.close(code=1011, reason="internal error")
    finally:
        presage_connected_clients = max(0, presage_connected_clients - 1)


@app.post("/audio")
async def ingest_audio(request: Request, label: str = Query("phrase")) -> JSONResponse:
    """Accept raw wav/PCM bytes, compute features, and store the latest summary."""

    global latest_audio_summary, last_audio_ts
    body = await request.body()
    audio_packet: AudioPacket = compute_audio_features(body, label=label)
    async with state_lock:
        latest_audio_summary = audio_packet.model_dump()
        last_audio_ts = audio_packet.timestamp

    print(
        f"[audio] label={label} mfcc_mean={audio_packet.mfcc_mean[:3]} jitter={audio_packet.jitter:.4f} shimmer={audio_packet.shimmer:.4f}"
    )

    return JSONResponse(content=audio_packet.model_dump())


@app.websocket("/live_state")
async def live_state(websocket: WebSocket) -> None:
    """Stream the latest summaries and triage/final output to the browser."""

    await websocket.accept()
    global live_state_clients, last_final_version_sent
    live_state_clients += 1
    try:
        while True:
            async with state_lock:
                presage_snapshot, simulated = _ensure_presage_summary()
                audio_snapshot = dict(latest_audio_summary)
                packet_age_ms = _age_ms(last_presage_ts)
                audio_age_ms = _age_ms(last_audio_ts)
                current_final_version = final_version
                final_report = dict(last_gemini_report)

            triage_output = await call_gemini_dummy(presage_snapshot, audio_snapshot)
            async with state_lock:
                last_triage_output.update(triage_output)

            live_payload = {
                "type": "live",
                "presage_summary": presage_snapshot,
                "audio_summary": audio_snapshot,
                "triage_output": triage_output,
                "debug": {
                    "packet_age_ms": packet_age_ms,
                    "using_simulated_presage": simulated,
                    "last_audio_age_ms": audio_age_ms,
                    "session_active": session_active,
                },
            }
            await websocket.send_json(live_payload)

            if current_final_version > last_final_version_sent and final_report:
                final_payload = {"type": "final", "gemini_report": final_report}
                await websocket.send_json(final_payload)
                last_final_version_sent = current_final_version

            await asyncio.sleep(0.3)
    except WebSocketDisconnect:
        pass
    except Exception:
        if websocket.application_state == WebSocketState.CONNECTED:
            await websocket.close(code=1011, reason="internal error")
    finally:
        live_state_clients = max(0, live_state_clients - 1)


@app.get("/health")
async def health() -> Dict[str, object]:
    return {
        "ok": True,
        "presage_packets_seen": presage_packets_seen,
        "last_presage_ts": last_presage_ts.isoformat() if last_presage_ts else None,
        "last_audio_ts": last_audio_ts.isoformat() if last_audio_ts else None,
        "presage_connected_clients": presage_connected_clients,
        "live_state_clients": live_state_clients,
    }


@app.get("/debug_state")
async def debug_state() -> Dict[str, object]:
    async with state_lock:
        presage_snapshot, simulated = _ensure_presage_summary()
        audio_snapshot = dict(latest_audio_summary)
        triage_snapshot = dict(last_triage_output)
        final_snapshot = dict(last_gemini_report)
    return {
        "latest_presage_summary": presage_snapshot,
        "latest_audio_summary": audio_snapshot,
        "last_triage_output": triage_snapshot,
        "last_gemini_report": final_snapshot,
        "buffer_sizes": {"presage": len(presage_buffer), "session": len(session_buffer)},
        "counters": {"presage_packets_seen": presage_packets_seen, "session_packets": session_packets},
        "session_active": session_active,
        "simulated": simulated,
    }


@app.get("/")
async def root_health() -> Dict[str, object]:
    return await health()
