"""Road connectivity monitoring endpoints."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Location, RiskPrediction, Road, User
from ..schemas.road import RoadStatusUpdate
from .deps import get_current_user
from ..services.emergency_service import compute_priority
from ..services.road_intelligence_service import (
    refresh_all_road_intelligence,
)

router = APIRouter(prefix="/roads", tags=["roads"])

STATUS_RISK_MAP = {
    "BLOCKED": "CRITICAL",
    "PARTIALLY_BLOCKED": "HIGH",
    "HIGH_RISK": "HIGH",
    "OPEN": "LOW",
}


def _out(road: Road) -> dict:
    return {
        "id": road.id,
        "name": road.name,
        "district": road.district,
        "state": road.state,
        "latitude": road.latitude,
        "longitude": road.longitude,
        "end_latitude": road.end_latitude,
        "end_longitude": road.end_longitude,
        "location_id": road.location_id,
        "status": road.status,
        "risk_level": road.risk_level,
        "updated_at": road.updated_at,
    }


@router.get("")
def list_roads(
    status: str | None = Query(default=None),
    state: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Road)
    if status:
        query = query.filter(Road.status == status.upper())
    if state:
        query = query.filter(Road.state == state)
    rows = query.order_by(Road.state, Road.name).all()
    return [_out(r) for r in rows]


@router.get("/summary")
def road_summary(db: Session = Depends(get_db)):
    """Status counts - dashboard card + analytics distribution."""
    rows = db.query(Road).all()
    counts = {"OPEN": 0, "HIGH_RISK": 0, "PARTIALLY_BLOCKED": 0, "BLOCKED": 0}
    for r in rows:
        counts[r.status] = counts.get(r.status, 0) + 1
    return {**{k.lower().replace("_", "_"): v for k, v in counts.items()}, "total": len(rows)}
@router.post("/refresh-intelligence")
def refresh_road_intelligence(
    db: Session = Depends(get_db),
):
    """
    Refresh road intelligence using the latest stored
    AI risk prediction for every monitored location.

    No fake data is generated.
    """

    result = refresh_all_road_intelligence(db)

    return {
        "message": "Road intelligence refreshed successfully",
        **result,
    }


@router.put("/{road_id}")
def update_road_status(
    road_id: int,
    payload: RoadStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update road status (field officer / admin).

    Also refreshes the emergency priority of the linked location so the
    response ranking reacts instantly to a newly blocked road.
    """
    if user.role not in ("ADMIN", "FIELD_OFFICER"):
        raise HTTPException(status_code=403, detail="Only officers can update roads")
    road = db.get(Road, road_id)
    if not road:
        raise HTTPException(status_code=404, detail="Road not found")

    road.status = payload.status
    road.risk_level = payload.risk_level or STATUS_RISK_MAP.get(payload.status, road.risk_level)
    road.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # Re-rank the linked location immediately.
    if road.location_id:
        location = db.get(Location, road.location_id)
        if location:
            latest = (
                db.query(RiskPrediction)
                .filter(RiskPrediction.location_id == location.id)
                .order_by(RiskPrediction.prediction_time.desc())
                .first()
            )
            compute_priority(db, location, latest.risk_score if latest else 0.0)

    db.commit()
    db.refresh(road)
    return _out(road)
