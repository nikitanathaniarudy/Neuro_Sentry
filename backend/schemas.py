"""Pydantic schemas for Presage packets used by the backend."""

from datetime import datetime, timezone
from typing import Annotated, Dict, List, Optional

from pydantic import BaseModel, Field


class PresagePacket(BaseModel):
    """Single Presage emission from the native bridge."""

    type: str = "vitals"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    heart_rate: Optional[float] = None
    breathing_rate: Optional[float] = None
    quality: Optional[float] = Field(
        default=None, description="Signal quality/confidence from the bridge"
    )
    blood_pressure: Optional[Dict[str, float]] = None
    face_points: List[Annotated[List[float], Field(min_length=2, max_length=3)]] = Field(
        default_factory=list,
        description="List of facial landmark points as [x, y, (z)]",
    )
    regions: Dict[str, float] = Field(
        default_factory=dict, description="Region activation/confidence scores"
    )


__all__ = ["PresagePacket"]
