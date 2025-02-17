import math
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Event, Location, EventClass
from app.schemas.schemas import EventCreate, EventOut, ClassificationResult
from app.services.classifier import classify_event

router = APIRouter(prefix="/events", tags=["Events"])

MOON_PHASES = [
    "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
    "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent",
]


def _moon_phase(dt: datetime) -> str:
    """Approximate lunar phase for a given date."""
    known_new = datetime(2000, 1, 6)
    cycle = 29.53058867
    days_since = (dt - known_new).days % cycle
    idx = int(days_since / cycle * 8) % 8
    return MOON_PHASES[idx]


@router.post("/", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(payload: EventCreate, db: AsyncSession = Depends(get_db)):
    """Log a new paranormal event."""
    loc_result = await db.execute(select(Location).where(Location.id == payload.location_id))
    if not loc_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Location not found")

    data = payload.model_dump()
    data["moon_phase"] = _moon_phase(payload.occurred_at)
    data["reported_at"] = datetime.utcnow()

    # auto-classify on creation
    clf = classify_event(
        event_id=0,
        kinetic=data["kinetic_score"],
        visual=data["visual_score"],
        thermal=data["thermal_score"],
        electronic=data["electronic_score"],
    )
    data["classification"] = clf.classification

    event = Event(**data)
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


@router.get("/", response_model=List[EventOut])
async def list_events(
    classification: Optional[EventClass] = None,
    verified: Optional[bool] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(Event)
    if classification:
        q = q.where(Event.classification == classification)
    if verified is not None:
        q = q.where(Event.verified == verified)
    q = q.order_by(Event.occurred_at.desc()).offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{event_id}", response_model=EventOut)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/{event_id}/classify", response_model=ClassificationResult)
async def classify(event_id: int, db: AsyncSession = Depends(get_db)):
    """Re-run classification engine on an existing event."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return classify_event(
        event_id=event.id,
        kinetic=event.kinetic_score,
        visual=event.visual_score,
        thermal=event.thermal_score,
        electronic=event.electronic_score,
    )


@router.patch("/{event_id}/verify", response_model=EventOut)
async def verify_event(event_id: int, db: AsyncSession = Depends(get_db)):
    """Mark event as verified by senior investigator."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.verified = True
    await db.flush()
    await db.refresh(event)
    return event
