"""Domain models for the Clarity Opsbot."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SensorReading(BaseModel):
    """Structured representation of an observation reported by units."""

    time: datetime
    mgrs: str = Field(
        default="UNKNOWN",
        description="Single MGRS string, uppercase, no spaces",
    )
    what: str
    amount: Optional[float] = None
    confidence: int = Field(ge=0, le=100)
    sensor_id: Optional[str] = None
    unit: Optional[str] = None
    observer_signature: str = Field(
        min_length=3,
        description="e.g., 'Sensor 1, Team A'",
    )


class FragoOrder(BaseModel):
    """Lightweight representation of a FRAGO order."""

    mission_overview: str
    situation: str
    execution: str
    sustainment: str
    command_and_signal: str

    def to_markdown(self) -> str:
        """Render the FRAGO order into a markdown-friendly string."""
        return (
            "FRAGO ORDER\n"
            "================\n"
            f"Mission Overview:\n{self.mission_overview}\n\n"
            f"Situation:\n{self.situation}\n\n"
            f"Execution:\n{self.execution}\n\n"
            f"Sustainment:\n{self.sustainment}\n\n"
            f"Command & Signal:\n{self.command_and_signal}"
        )
