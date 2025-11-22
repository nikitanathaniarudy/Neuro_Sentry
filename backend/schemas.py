"""Pydantic schemas for Presage packets, audio summaries, and triage output."""

from typing import Annotated, Dict, List, Optional
from datetime import datetime


from pydantic import BaseModel, Field, confloat, conint


class PresagePacket(BaseModel):
    """Single Presage emission from the native bridge."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    heart_rate: Optional[float] = None
    breathing_rate: Optional[float] = None
    quality: Optional[float] = Field(
        default=None, description="Signal quality/confidence from the bridge"
    )
    face_points: List[Annotated[List[float], Field(min_length=2, max_length=3)]] = Field(
        default_factory=list,
        description="List of facial landmark points as [x, y, (z)]",
    )
    regions: Dict[str, float] = Field(
        default_factory=dict, description="Region activation/confidence scores"
    )
    is_simulated: bool = False # New field to indicate if this packet is from a simulator


class AudioPacket(BaseModel):
    """Lightweight summary of an audio clip."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    label: str = "phrase"
    duration: float
    sample_rate: int
    mfcc_mean: List[float]
    jitter: float
    shimmer: float
    energy: float


class TriageOutput(BaseModel):
    """Structured triage response expected from Gemini."""

    overall_risk: confloat(ge=0, le=1)
    triage_level: conint(ge=1, le=5)
    confidence: confloat(ge=0, le=1)
    rationale_short: str
    ui_directives: Dict[str, object] = Field(
        description="UI hints such as alert color and highlighted facial regions"
    )


class LiveState(BaseModel):
    presage_summary: Dict[str, object]
    audio_summary: Dict[str, object]
    triage_output: TriageOutput


__all__ = [
    "PresagePacket",
    "AudioPacket",
    "TriageOutput",
    "LiveState",
]
