from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Event, Location, ThreatLevel
from app.schemas.schemas import EventOut, LocationCreate, LocationOut, LocationUpdate

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get("/", response_model=List[LocationOut])
async def list_locations(
    country_code: Optional[str] = None,
    threat_level: Optional[ThreatLevel] = None,
    tag: Optional[str] = None,
    active_only: bool = True,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List haunted locations with optional filters."""
    q = select(Location)
    if active_only:
        q = q.where(Location.is_active is True)
    if country_code:
        q = q.where(Location.country_code == country_code.upper())
    if threat_level:
        q = q.where(Location.threat_level == threat_level)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    locations = result.scalars().all()
    out = []
    for loc in locations:
        events_result = await db.execute(
            select(func.count()).where(Event.location_id == loc.id)
        )
        count = events_result.scalar() or 0
        loc_dict = {c.name: getattr(loc, c.name) for c in loc.__table__.columns}
        loc_dict["event_count"] = count
        out.append(LocationOut(**loc_dict))
    return out


@router.post("/", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
async def create_location(
    payload: LocationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new haunted location."""
    location = Location(**payload.model_dump())
    db.add(location)
    await db.flush()
    await db.refresh(location)
    loc_dict = {c.name: getattr(location, c.name) for c in location.__table__.columns}
    loc_dict["event_count"] = 0
    return LocationOut(**loc_dict)


@router.get("/{location_id}", response_model=LocationOut)
async def get_location(location_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Location).where(Location.id == location_id))
    loc = result.scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    events_result = await db.execute(
        select(func.count()).where(Event.location_id == loc.id)
    )
    count = events_result.scalar() or 0
    loc_dict = {c.name: getattr(loc, c.name) for c in loc.__table__.columns}
    loc_dict["event_count"] = count
    return LocationOut(**loc_dict)


@router.patch("/{location_id}", response_model=LocationOut)
async def update_location(
    location_id: int,
    payload: LocationUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Location).where(Location.id == location_id))
    loc = result.scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(loc, field, value)
    await db.flush()
    events_result = await db.execute(
        select(func.count()).where(Event.location_id == loc.id)
    )
    count = events_result.scalar() or 0
    loc_dict = {c.name: getattr(loc, c.name) for c in loc.__table__.columns}
    loc_dict["event_count"] = count
    return LocationOut(**loc_dict)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(location_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Location).where(Location.id == location_id))
    loc = result.scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    await db.delete(loc)


@router.get("/{location_id}/events", response_model=List[EventOut])
async def get_location_events(
    location_id: int,
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Event)
        .where(Event.location_id == location_id)
        .order_by(Event.occurred_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
