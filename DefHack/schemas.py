from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import re

_MGRS_RE = re.compile(r"^[0-9]{1,2}[C-HJ-NP-X][A-HJ-NP-Z]{2}[0-9]{2,10}$")

class SensorIn(BaseModel):
    time: datetime
    mgrs: str = Field(description="Single MGRS string, uppercase, no spaces")
    what: str
    amount: float | None = None
    confidence: int = Field(ge=0, le=100)
    sensor_id: str
    unit: str | None = None
    observer_signature: str = Field(min_length=3, description="e.g., 'Sensor 1, Team A'")

    @field_validator('mgrs')
    @classmethod
    def validate_mgrs(cls, v: str) -> str:
        v2 = v.replace(" ", "").upper()
        if not _MGRS_RE.match(v2):
            raise ValueError("Invalid MGRS format")
        return v2

class SensorReading(BaseModel):
    time: datetime
    mgrs: str = Field(description="Single MGRS string, uppercase, no spaces")
    what: str
    amount: float | None = None
    confidence: int = Field(ge=0, le=100)
    sensor_id: str
    unit: str | None = None
    observer_signature: str = Field(min_length=3, description="e.g., 'Sensor 1, Team A'")

    @field_validator('mgrs')
    @classmethod
    def validate_mgrs(cls, v: str) -> str:
        v2 = v.replace(" ", "").upper()
        if not _MGRS_RE.match(v2):
            raise ValueError("Invalid MGRS format")
        return v2