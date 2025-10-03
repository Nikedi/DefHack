from typing import Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class SensorReading(BaseModel):
    time: datetime
    mgrs: str = Field(description="Single MGRS string, uppercase, no spaces")
    what: str
    amount: float | None = None
    confidence: int = Field(ge=0, le=100)
    sensor_id: str
    unit: str | None = None
    observer_signature: str = Field(min_length=3, description="e.g., 'Sensor 1, Team A'")


class SensorSchema:
    """Superclass for schemas produced from arbitrary sensor input.

    Provides a factory for algorithms that convert sensor input into schema instances
    and a helper to build canonical :class:`SensorReading` objects.
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
        mgrs: str,
        what: str,
        sensor_id: str,
        observer_signature: str,
        amount: float | None = None,
        unit: str | None = None,
    ) -> SensorReading:
        """Convert this schema instance into a :class:`SensorReading`."""
        return SensorReading(
            time=self.Timestamp,
            mgrs=mgrs,
            what=what,
            amount=amount if amount is not None else float(self.Count),
            confidence=int(round(self.Confidence)),
            sensor_id=sensor_id,
            unit=unit,
            observer_signature=observer_signature,
        )

    def to_dict(self, **kwargs) -> SensorReading:
        """Return a :class:`SensorReading` representation of this schema."""
        return self.to_sensor_reading(**kwargs)
	