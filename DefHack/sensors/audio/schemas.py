from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..SensorSchema import SensorSchema


@dataclass
class AcousticDroneSchema(SensorSchema):
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        *,
        timestamp: datetime,
        place: str,
        harmonic_count: int,
        detection_type: str,
        confidence: float,
        produced_by: str,
        metadata: Dict[str, Any],
    ) -> None:
        super().__init__(
            Timestamp=timestamp.isoformat(),
            Place=place,
            Count=harmonic_count,
            Type=detection_type,
            Confidence=confidence,
            Produced_by=produced_by,
        )
        self.metadata = metadata

    @property
    def summary(self) -> str:
        return self.metadata.get("description", "No observable rotor signature")

    @property
    def detection_timestamp(self) -> datetime:
        raw = self.Timestamp
        if isinstance(raw, datetime):
            return raw
        try:
            return datetime.fromisoformat(raw)
        except ValueError:  # pragma: no cover - defensive
            return datetime.now(tz=timezone.utc)

    def to_sensor_message(
        self,
        *,
        mgrs: Optional[str] = None,
        sensor_id: Optional[str] = None,
        observer_signature: str = "AcousticDetector",
        unit: Optional[str] = None,
        what: Optional[str] = None,
        amount: Optional[float] = None,
    ):
        description = what if what is not None else self.summary
        harmonic_count = float(self.metadata.get("harmonic_count", self.Count))
        narrative = self.metadata.get("narrative")
        return self.to_sensor_reading(
            mgrs=mgrs,
            what=description,
            amount=amount if amount is not None else harmonic_count,
            sensor_id=sensor_id,
            observer_signature=observer_signature,
            unit=unit,
            original_message=narrative,
        )


def build_no_detection_schema(source: str) -> AcousticDroneSchema:
    now = datetime.now(tz=timezone.utc)
    metadata = {
        "source": source,
        "description": "No rotor signature detected",
        "confidence_pct": 0,
        "harmonic_count": 0,
        "narrative": "Signal analysis did not reveal periodic narrow-band energy indicative of UAV rotors.",
    }
    return AcousticDroneSchema(
        timestamp=now,
        place="UNKNOWN",
        harmonic_count=0,
        detection_type="RotorAcousticDetection",
        confidence=0,
        produced_by="AcousticBPF-1.0",
        metadata=metadata,
    )
