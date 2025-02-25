from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class ThreatLevel(PyEnum):
    BENIGN = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    EXTREME = 5


class EventClass(PyEnum):
    UNKNOWN = "unknown"
    POLTERGEIST = "poltergeist"
    APPARITION = "apparition"
    INFRASOUND = "infrasound"
    ELECTRICAL = "electrical"
    RESIDUAL = "residual"
    INTELLIGENT = "intelligent"


class InvestigatorRole(PyEnum):
    FIELD_AGENT = "field_agent"
    ANALYST = "analyst"
    ADMIN = "admin"


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    address = Column(String(500))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    country_code = Column(String(3), index=True)
    threat_level = Column(Enum(ThreatLevel), default=ThreatLevel.UNKNOWN if False else ThreatLevel.LOW)
    is_active = Column(Boolean, default=True)
    first_reported = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    tags = Column(JSON, default=list)

    events = relationship("Event", back_populates="location", cascade="all, delete-orphan")

    @property
    def event_count(self):
        return len(self.events)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    investigator_id = Column(Integer, ForeignKey("investigators.id"), nullable=True)

    title = Column(String(300), nullable=False)
    description = Column(Text)
    occurred_at = Column(DateTime, nullable=False, index=True)
    reported_at = Column(DateTime, default=datetime.utcnow)

    witness_count = Column(Integer, default=0)
    classification = Column(Enum(EventClass), default=EventClass.UNKNOWN)

    # Scoring axes (0.0 - 1.0)
    kinetic_score = Column(Float, default=0.0)
    visual_score = Column(Float, default=0.0)
    thermal_score = Column(Float, default=0.0)
    electronic_score = Column(Float, default=0.0)

    evidence = Column(JSON, default=list)   # ["photo", "audio", "emf_reading"]
    moon_phase = Column(String(30), nullable=True)
    verified = Column(Boolean, default=False)

    location = relationship("Location", back_populates="events")
    investigator = relationship("Investigator", back_populates="events")


class Investigator(Base):
    __tablename__ = "investigators"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(Enum(InvestigatorRole), default=InvestigatorRole.FIELD_AGENT)
    codename = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    cases_count = Column(Integer, default=0)

    events = relationship("Event", back_populates="investigator")
