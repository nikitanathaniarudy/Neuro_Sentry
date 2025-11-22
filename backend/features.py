"""Deterministic feature helpers for Presage windows and audio clips."""

from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Deque, Dict, Iterable, List, Tuple

import librosa
import numpy as np

from schemas import AudioPacket, PresagePacket


WINDOW_SECONDS = 3.0


def _safe_mean(values: Iterable[float]) -> float:
    arr = np.fromiter(values, dtype=float, count=-1)
    return float(arr.mean()) if arr.size else 0.0


def trim_presage_window(
    buffer: Deque[Tuple[datetime, PresagePacket]], window_seconds: float = WINDOW_SECONDS
) -> None:
    """Remove packets older than the configured rolling window."""

    cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
    while buffer and buffer[0][0] < cutoff:
        buffer.popleft()


def summarize_presage_window(
    buffer: Deque[Tuple[datetime, PresagePacket]],
    window_seconds: float = WINDOW_SECONDS,
) -> Dict[str, object]:
    """Aggregate vitals and regional data into a compact summary."""

    trim_presage_window(buffer, window_seconds)
    packets = [p for _, p in buffer]
    if not packets:
        return {
            "window_seconds": window_seconds,
            "count": 0,
            "heart_rate": 0.0,
            "breathing_rate": 0.0,
            "quality": 0.0,
            "top_regions": [],
        "point_count": 0,
    }

    heart_rates = [p.heart_rate for p in packets if p.heart_rate is not None]
    breaths = [p.breathing_rate for p in packets if p.breathing_rate is not None]
    qualities = [p.quality for p in packets if p.quality is not None]
    region_totals: Dict[str, List[float]] = {}
    for packet in packets:
        for region, value in packet.regions.items():
            region_totals.setdefault(region, []).append(float(value))

    region_means = {k: _safe_mean(v) for k, v in region_totals.items()}
    top_regions = sorted(region_means.items(), key=lambda kv: kv[1], reverse=True)[:3]

    latest_points = packets[-1].face_points if packets[-1].face_points else []
    return {
        "window_seconds": window_seconds,
        "count": len(packets),
        "heart_rate": _safe_mean(heart_rates),
        "breathing_rate": _safe_mean(breaths),
        "quality": _safe_mean(qualities),
        "top_regions": [{"region": r, "score": s} for r, s in top_regions],
        "point_count": len(latest_points),
        "face_points": latest_points,
        "last_timestamp": packets[-1].timestamp.isoformat(),
    }


def build_simulated_presage(now: datetime | None = None) -> Dict[str, object]:
    """Return a stable simulated presage summary when no live packets arrive."""

    now = now or datetime.now(timezone.utc)
    return {
        "window_seconds": WINDOW_SECONDS,
        "count": 1,
        "heart_rate": 72.0,
        "breathing_rate": 14.0,
        "quality": 0.5,
        "top_regions": [],
        "point_count": 0,
        "face_points": [],
        "last_timestamp": now.isoformat(),
    }


def _jitter_shimmer_proxies(y: np.ndarray) -> Tuple[float, float]:
    """Approximate jitter/shimmer proxies from waveform stability."""

    if y.size < 4:
        return 0.0, 0.0
    # Jitter proxy: stability of zero-crossings
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    jitter = float(np.std(np.diff(zcr)))

    # Shimmer proxy: change in amplitude envelope
    envelope = np.abs(librosa.onset.onset_strength(y=y))
    shimmer = float(np.std(np.diff(envelope))) if envelope.size > 1 else 0.0
    return jitter, shimmer


def compute_audio_features(audio_bytes: bytes, label: str = "phrase") -> AudioPacket:
    """Derive MFCC statistics and stability proxies from raw wav/PCM bytes."""

    if not audio_bytes:
        return AudioPacket(
            label=label,
            duration=0.0,
            sample_rate=16000,
            mfcc_mean=[0.0] * 13,
            jitter=0.0,
            shimmer=0.0,
            energy=0.0,
        )

    y, sr = librosa.load(BytesIO(audio_bytes), sr=16000, mono=True)
    duration = float(len(y) / sr) if sr else 0.0

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_mean = mfcc.mean(axis=1).tolist()

    jitter, shimmer = _jitter_shimmer_proxies(y)
    energy = float(np.mean(y**2)) if y.size else 0.0

    return AudioPacket(
        label=label,
        duration=duration,
        sample_rate=sr,
        mfcc_mean=mfcc_mean,
        jitter=jitter,
        shimmer=shimmer,
        energy=energy,
    )


def summarize_state_for_model(presage_summary: Dict[str, object], audio_summary: Dict[str, object]) -> str:
    """Compact JSON string for prompt building with Gemini."""

    payload = {
        "presage": presage_summary,
        "audio": audio_summary,
    }
    return json.dumps(payload, ensure_ascii=True)
