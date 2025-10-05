from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import re

_MGRS_RE = re.compile(r"^[0-9]{1,2}[C-HJ-NP-X][A-HJ-NP-Z]{2}[0-9]{2,10}$")

# ===== TACTICAL SENSOR OBSERVATIONS =====
# Used for field reports, tactical sightings, real-time observations

class SensorObservationIn(BaseModel):
    """Input schema for tactical sensor observations from the field"""
    time: datetime = Field(description="When the observation was made (ISO 8601)")
    mgrs: str | None = Field(None, description="Location in MGRS format (e.g., '35VLG8472571866') or null if unknown")
    what: str = Field(description="What was observed (e.g., 'T-72 Tank', 'Infantry Squad')")
    amount: float | None = Field(None, description="Number/quantity observed")
    confidence: int = Field(ge=0, le=100, description="Observer confidence level (0-100)")
    sensor_id: str | None = Field(None, description="ID of sensor/observer equipment or null for human observers")
    unit: str | None = Field(None, description="Observing unit (e.g., 'Alpha Company, 2nd Platoon')")
    observer_signature: str = Field(min_length=3, description="Observer identification (e.g., 'CallSign' or 'FirstnameLastname')")
    original_message: str | None = Field(None, description="Original message text or null for sensor data without text")

    @field_validator('mgrs')
    @classmethod
    def validate_mgrs(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v2 = v.replace(" ", "").upper()
        if not _MGRS_RE.match(v2):
            raise ValueError("Invalid MGRS format")
        return v2

class SensorObservation(BaseModel):
    """Database schema for stored tactical sensor observations"""
    time: datetime = Field(description="When the observation was made (ISO 8601)")
    mgrs: str | None = Field(None, description="Location in MGRS format (e.g., '35VLG8472571866') or null if unknown")
    what: str = Field(description="What was observed (e.g., 'T-72 Tank', 'Infantry Squad')")
    amount: float | None = Field(None, description="Number/quantity observed")
    confidence: int = Field(ge=0, le=100, description="Observer confidence level (0-100)")
    sensor_id: str | None = Field(None, description="ID of sensor/observer equipment or null for human observers")
    unit: str | None = Field(None, description="Observing unit (e.g., 'Alpha Company, 2nd Platoon')")
    observer_signature: str = Field(min_length=3, description="Observer identification (e.g., 'CallSign' or 'FirstnameLastname')")
    original_message: str | None = Field(None, description="Original message text or null for sensor data without text")

    @field_validator('mgrs')
    @classmethod
    def validate_mgrs(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v2 = v.replace(" ", "").upper()
        if not _MGRS_RE.match(v2):
            raise ValueError("Invalid MGRS format")
        return v2

# ===== INTELLIGENCE DOCUMENTS =====  
# Used for strategic documents, PDFs, doctrinal materials, reports

class IntelligenceDocumentMetadata(BaseModel):
    """Metadata schema for intelligence document uploads"""
    title: str = Field(description="Document title")
    version: str | None = Field(None, description="Document version")
    lang: str | None = Field("en", description="Document language (ISO 639-1)")
    origin: str | None = Field(None, description="Source organization")
    adversary: str | None = Field(None, description="Adversary/subject focus")
    published_at: str | None = Field(None, description="Publication date (YYYY-MM-DD)")
    classification: str | None = Field("UNCLASSIFIED", description="Security classification")
    document_type: str | None = Field(None, description="Type: 'doctrinal', 'tactical', 'strategic', 'technical'")