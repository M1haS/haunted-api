from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.models import EventClass, InvestigatorRole, ThreatLevel

# ── Location ──────────────────────────────────────────────────────────────────

class LocationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, examples=["Overtoun Bridge"])
    address: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    country_code: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None
    tags: List[str] = []

    @field_validator("tags")
    @classmethod
    def limit_tags(cls, v):
        if len(v) > 10:
            raise ValueError("Max 10 tags per location")
        return [t.lower().strip() for t in v]


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    threat_level: Optional[ThreatLevel] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


class LocationOut(BaseModel):
    id: int
    name: str
    address: Optional[str]
    latitude: float
    longitude: float
    country_code: Optional[str]
    threat_level: ThreatLevel
    is_active: bool
    first_reported: datetime
    tags: List[str]
    event_count: int = 0

    model_config = {"from_attributes": True}


# ── Event ─────────────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    location_id: int
    title: str = Field(..., min_length=3, max_length=300)
    description: Optional[str] = None
    occurred_at: datetime
    witness_count: int = Field(0, ge=0, le=10000)
    kinetic_score: float = Field(0.0, ge=0, le=1)
    visual_score: float = Field(0.0, ge=0, le=1)
    thermal_score: float = Field(0.0, ge=0, le=1)
    electronic_score: float = Field(0.0, ge=0, le=1)
    evidence: List[str] = []


class EventOut(BaseModel):
    id: int
    location_id: int
    title: str
    description: Optional[str]
    occurred_at: datetime
    reported_at: datetime
    witness_count: int
    classification: EventClass
    kinetic_score: float
    visual_score: float
    thermal_score: float
    electronic_score: float
    evidence: List[str]
    moon_phase: Optional[str]
    verified: bool

    model_config = {"from_attributes": True}


class ClassificationResult(BaseModel):
    event_id: int
    classification: EventClass
    confidence: float
    threat_level: ThreatLevel
    dominant_axis: str
    reasoning: str


# ── Stats ─────────────────────────────────────────────────────────────────────

class Hotspot(BaseModel):
    location_id: int
    location_name: str
    latitude: float
    longitude: float
    event_count: int
    avg_threat: float
    last_activity: Optional[datetime]


class MoonPhaseStats(BaseModel):
    phase: str
    event_count: int
    avg_witness_count: float
    verified_ratio: float


# ── Auth ──────────────────────────────────────────────────────────────────────

class InvestigatorCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8)
    codename: Optional[str] = None


class InvestigatorOut(BaseModel):
    id: int
    username: str
    email: str
    role: InvestigatorRole
    codename: Optional[str]
    is_active: bool
    cases_count: int

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
