"""Emergency response priority endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import EmergencyPriority, Location
from .deps import get_current_user
from ..services.emergency_service import compute_all_priorities

router = APIRouter(prefix="/emergency", tags=["emergency"])


def _out(row: EmergencyPriority, location: Location | None, risk=None) -> dict:
    return {
        "id": row.id,
        "location_id": row.location_id,
        "priority_level": row.priority_level,
        "priority_score": row.priority_score,
        "reason": row.reason,
        "created_at": row.created_at,
        "risk_level": risk.risk_level if risk else None,
        "risk_score": risk.risk_score if risk else None,
        "location": {
            "id": location.id,
            "name": location.name,
            "district": location.district,
            "state": location.state,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "elevation": location.elevation,
        } if location else None,
    }


def _rows_with_risk(db: Session, rows):
    from ..utils.queries import latest_risk_by_location

    risk_map = latest_risk_by_location(db)
    loc_map = {loc.id: loc for loc in db.query(Location).all()}
    return [_out(r, loc_map.get(r.location_id), risk_map.get(r.location_id)) for r in rows]


@router.get("/priorities")
def list_priorities(db: Session = Depends(get_db)):
    """Ranked emergency response list, most urgent first."""
    rows = db.query(EmergencyPriority).order_by(
        EmergencyPriority.priority_score.desc(),
        EmergencyPriority.created_at.asc(),
    ).all()
    return _rows_with_risk(db, rows)


@router.post("/recompute")
def recompute_priorities(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Recompute the full emergency ranking from live risk + road status."""
    rows = compute_all_priorities(db)
    db.commit()
    return _rows_with_risk(db, rows)
