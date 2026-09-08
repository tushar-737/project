"""Reusable row-fetching helpers for routers."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import EnvironmentalData, Location, RiskPrediction


def latest_environment_by_location(db: Session) -> dict[int, EnvironmentalData]:
    """Latest environmental sample per location (keyed by location_id)."""
    max_ids = db.query(
        func.max(EnvironmentalData.id).label("id")
    ).group_by(EnvironmentalData.location_id).subquery()
    rows = db.query(EnvironmentalData).filter(
        EnvironmentalData.id.in_(db.query(max_ids.c.id))
    ).all()
    return {r.location_id: r for r in rows}


def latest_risk_by_location(db: Session) -> dict[int, RiskPrediction]:
    """Latest risk prediction per location (keyed by location_id)."""
    max_ids = db.query(
        func.max(RiskPrediction.id).label("id")
    ).group_by(RiskPrediction.location_id).subquery()
    rows = db.query(RiskPrediction).filter(
        RiskPrediction.id.in_(db.query(max_ids.c.id))
    ).all()
    return {r.location_id: r for r in rows}


def active_locations(db: Session) -> list[Location]:
    return db.query(Location).filter(Location.is_active.is_(True)).order_by(Location.name).all()


def location_summaries(db: Session) -> list[dict]:
    """Full monitoring picture: location + latest env + latest risk."""
    from ..schemas.environment import EnvironmentalDataOut
    from ..schemas.risk import RiskPredictionOut

    env_map = latest_environment_by_location(db)
    risk_map = latest_risk_by_location(db)

    out = []
    for loc in active_locations(db):
        out.append({
            **{c.name: getattr(loc, c.name) for c in Location.__table__.columns},
            "latest_environment": (
                EnvironmentalDataOut.model_validate(env_map[loc.id]) if loc.id in env_map else None
            ),
            "latest_risk": (
                RiskPredictionOut.from_row(risk_map[loc.id]) if loc.id in risk_map else None
            ),
        })
    return out
