"""Pydantic schemas for Presage session uploads and Gemini output."""

from datetime import datetime, timezone
from typing import Annotated, Dict, List, Optional

from pydantic import BaseModel, Field, confloat, conint


class PresagePacket(BaseModel):
    """Single Presage emission from the native bridge."""

    type: str = "vitals"
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


class SessionUpload(BaseModel):
    """Full session upload with raw packets."""

    type: str = "session_upload"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    device: str = "iphone"
    packets: List[PresagePacket]


class GeminiReport(BaseModel):
    risk_level: str
    stroke_probability: confloat(ge=0, le=1)
    summary: str
    recommendation: str
    confidence: confloat(ge=0, le=1)


__all__ = ["PresagePacket", "SessionUpload", "GeminiReport"]
