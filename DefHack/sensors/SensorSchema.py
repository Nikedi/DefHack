from typing import Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class SensorObservationIn(BaseModel):
    """Input schema for tactical sensor observations from the field"""

    time: datetime = Field(description="When the observation was made (ISO 8601)")
    mgrs: str | None = Field(
        None,
        description="Location in MGRS format (e.g., '35VLG8472571866') or null if unknown",
    )
    what: str = Field(description="What was observed (e.g., 'T-72 Tank', 'Infantry Squad')")
    amount: float | None = Field(None, description="Number/quantity observed")
    confidence: int = Field(
        ge=0,
        le=100,
        description="Observer confidence level (0-100)",
    )
    sensor_id: str | None = Field(
        None,
        description="ID of sensor/observer equipment or null for human observers",
    )
    unit: str | None = Field(
        None,
        description="Observing unit (e.g., 'Alpha Company, 2nd Platoon')",
    )
    observer_signature: str = Field(
        min_length=3,
        description="Observer identification (e.g., 'CallSign' or 'FirstnameLastname')",
    )
    original_message: str | None = Field(
        None,
        description="Original message text or null for sensor data without text",
    )


class SensorSchema:
    """Superclass for schemas produced from arbitrary sensor input.

    Provides a factory for algorithms that convert sensor input into schema instances
    and a helper to build canonical :class:`SensorObservationIn` objects.
    """

    # Registry for conversion algorithms: {algorithm_name: callable}
    _algorithm_factory: Dict[str, Any] = {}

    @classmethod
    def register_algorithm(cls, name: str, algorithm: Any):
        """Register a conversion algorithm by name."""
        if "_algorithm_factory" not in cls.__dict__:
            cls._algorithm_factory = dict(cls._algorithm_factory)
        cls._algorithm_factory[name] = algorithm

    @classmethod
    def from_sensor(cls, sensor_input: Any, algorithm: str = None, **kwargs) -> 'SensorSchema':
        """Convert sensor input to a schema using the specified algorithm."""
        factory = cls.__dict__.get("_algorithm_factory", cls._algorithm_factory)
        if not factory:
            raise ValueError("No algorithms registered for schema conversion.")
        if algorithm is None:
            algorithm = next(iter(factory))
        if algorithm not in factory:
            raise ValueError(f"Algorithm '{algorithm}' not registered.")
        return factory[algorithm](sensor_input, **kwargs)

    def __init__(self, Timestamp: str, Place: str, Count: int, Type: str, Confidence: float, Produced_by: str):
        self.Timestamp = Timestamp
        self.Place = Place
        self.Count = Count
        self.Type = Type
        self.Confidence = Confidence
        self.Produced_by = Produced_by

    def to_sensor_reading(
        self,
        *,
        mgrs: str | None,
        what: str,
        sensor_id: str | None,
        observer_signature: str,
        amount: float | None = None,
        unit: str | None = None,
        original_message: str | None = None,
    ) -> SensorObservationIn:
        """Convert this schema instance into a :class:`SensorObservationIn`."""
        return SensorObservationIn(
            time=self.Timestamp,
            mgrs=mgrs,
            what=what,
            amount=amount if amount is not None else float(self.Count),
            confidence=int(round(self.Confidence)),
            sensor_id=sensor_id,
            unit=unit,
            observer_signature=observer_signature,
            original_message=original_message,
        )

    def to_dict(self, **kwargs) -> SensorObservationIn:
        """Return a :class:`SensorObservationIn` representation of this schema."""
        return self.to_sensor_reading(**kwargs)
	