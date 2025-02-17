from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.models import Location, Event, ThreatLevel
from app.schemas.schemas import Hotspot, MoonPhaseStats
from app.services.heatmap import cluster_hotspots

router = APIRouter(prefix="/stats", tags=["Statistics"])

THREAT_VALUES = {
    ThreatLevel.BENIGN: 1,
    ThreatLevel.LOW: 2,
    ThreatLevel.MODERATE: 3,
    ThreatLevel.HIGH: 4,
    ThreatLevel.EXTREME: 5,
}


@router.get("/hotspots", response_model=List[Hotspot])
async def get_hotspots(
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Top haunted locations ranked by event count."""
    q = (
        select(
            Location,
            func.count(Event.id).label("event_count"),
            func.max(Event.occurred_at).label("last_activity"),
        )
        .outerjoin(Event, Event.location_id == Location.id)
        .where(Location.is_active == True)
        .group_by(Location.id)
        .order_by(func.count(Event.id).desc())
        .limit(limit)
    )
    result = await db.execute(q)
    rows = result.all()

    hotspots = []
    for loc, count, last in rows:
        hotspots.append(
            Hotspot(
                location_id=loc.id,
                location_name=loc.name,
                latitude=loc.latitude,
                longitude=loc.longitude,
                event_count=count,
                avg_threat=THREAT_VALUES.get(loc.threat_level, 1),
                last_activity=last,
            )
        )
    return hotspots


@router.get("/clusters")
async def get_clusters(
    radius_km: float = Query(50.0, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Cluster nearby locations into geographic hotzone groups."""
    q = (
        select(
            Location,
            func.count(Event.id).label("event_count"),
            func.max(Event.occurred_at).label("last_activity"),
        )
        .outerjoin(Event, Event.location_id == Location.id)
        .where(Location.is_active == True)
        .group_by(Location.id)
    )
    result = await db.execute(q)
    rows = result.all()
    hotspots = [
        Hotspot(
            location_id=loc.id,
            location_name=loc.name,
            latitude=loc.latitude,
            longitude=loc.longitude,
            event_count=cnt,
            avg_threat=THREAT_VALUES.get(loc.threat_level, 1),
            last_activity=last,
        )
        for loc, cnt, last in rows
    ]
    return cluster_hotspots(hotspots, radius_km=radius_km)


@router.get("/moon-phase", response_model=List[MoonPhaseStats])
async def get_moon_phase_stats(db: AsyncSession = Depends(get_db)):
    """Activity breakdown by lunar phase."""
    result = await db.execute(select(Event))
    events = result.scalars().all()

    phase_data: dict = {}
    for ev in events:
        phase = ev.moon_phase or "Unknown"
        if phase not in phase_data:
            phase_data[phase] = {"count": 0, "witnesses": 0, "verified": 0}
        phase_data[phase]["count"] += 1
        phase_data[phase]["witnesses"] += ev.witness_count
        phase_data[phase]["verified"] += int(ev.verified)

    stats = []
    for phase, data in sorted(phase_data.items(), key=lambda x: -x[1]["count"]):
        c = data["count"]
        stats.append(
            MoonPhaseStats(
                phase=phase,
                event_count=c,
                avg_witness_count=round(data["witnesses"] / c, 2),
                verified_ratio=round(data["verified"] / c, 3),
            )
        )
    return stats


@router.get("/summary")
async def summary(db: AsyncSession = Depends(get_db)):
    """Quick dashboard numbers."""
    loc_count = (await db.execute(select(func.count()).select_from(Location))).scalar()
    event_count = (await db.execute(select(func.count()).select_from(Event))).scalar()
    verified_count = (
        await db.execute(select(func.count()).where(Event.verified == True))
    ).scalar()
    extreme_count = (
        await db.execute(
            select(func.count()).where(Location.threat_level == ThreatLevel.EXTREME)
        )
    ).scalar()

    return {
        "total_locations": loc_count,
        "total_events": event_count,
        "verified_events": verified_count,
        "extreme_threat_locations": extreme_count,
    }
