"""Alerts endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Alert, Location
from .deps import get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _out(alert: Alert, location: Location | None) -> dict:
    return {
        "id": alert.id,
        "location_id": alert.location_id,
        "location_name": location.name if location else None,
        "district": location.district if location else None,
        "state": location.state if location else None,
        "risk_level": alert.risk_level,
        "risk_score": alert.risk_score,
        "message": alert.message,
        "status": alert.status,
        "created_at": alert.created_at,
    }


@router.get("")
def list_alerts(
    status: str | None = Query(default=None),
    level: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status.upper())
    if level:
        query = query.filter(Alert.risk_level == level.upper())
    rows = query.order_by(Alert.created_at.desc()).limit(limit).all()
    loc_map = {loc.id: loc for loc in db.query(Location).all()}
    return [_out(a, loc_map.get(a.location_id)) for a in rows]


@router.get("/summary")
def alert_summary(db: Session = Depends(get_db)):
    """Counts of active alerts per risk level."""
    rows = db.query(Alert).filter(Alert.status == "ACTIVE").all()
    return {
        "high": sum(1 for a in rows if a.risk_level == "HIGH"),
        "critical": sum(1 for a in rows if a.risk_level == "CRITICAL"),
        "total": len(rows),
    }


@router.put("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Manually mark an alert as RESOLVED (situation cleared by field team)."""
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    from ..models.alert import utcnow
    alert.status = "RESOLVED"
    alert.resolved_at = utcnow()
    db.commit()
    location = db.get(Location, alert.location_id)
    return _out(alert, location)
