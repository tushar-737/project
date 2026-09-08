"""Emergency priority engine.

Computes an emergency response ranking for every monitored location.

Priority model (0-100):
    risk_score (55%)     - current AI risk of the site
    road isolation (25%) - worst road status serving the site
                           (BLOCKED=1.0, PARTIALLY_BLOCKED=0.7,
                            HIGH_RISK=0.45, OPEN=0.0)
    population (12%)     - population_factor of the location
    isolation (8%)       - remoteness factor of the location

Bands:
    76-100  PRIORITY 1 - Immediate response
    51-75   PRIORITY 2 - Urgent response
    0-50    PRIORITY 3 - Monitoring required
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import EmergencyPriority, Road

ROAD_ISOLATION_SCORE = {
    "BLOCKED": 1.0,
    "PARTIALLY_BLOCKED": 0.7,
    "HIGH_RISK": 0.45,
    "OPEN": 0.0,
}


def priority_for_score(score: float) -> str:
    if score >= 76:
        return "PRIORITY 1"
    if score >= 51:
        return "PRIORITY 2"
    return "PRIORITY 3"


def _describe(level: str) -> str:
    return {
        "PRIORITY 1": "Immediate response required",
        "PRIORITY 2": "Urgent response required",
        "PRIORITY 3": "Monitoring required",
    }[level]


def compute_priority(db: Session, location, risk_score: float) -> EmergencyPriority:
    """Compute and store the priority record for one location."""
    roads = (
        db.query(Road)
        .filter(Road.location_id == location.id)
        .order_by(Road.updated_at.desc())
        .all()
    )
    worst_road = roads[0] if roads else None
    worst_score = 0.0
    for road in roads:
        s = ROAD_ISOLATION_SCORE.get(road.status, 0.0)
        if s >= worst_score:
            worst_score = s
            worst_road = road

    road_detail = "no monitored road"
    if worst_road:
        road_detail = f"{worst_road.name} ({worst_road.status})"

    score = (
        0.55 * min(100.0, risk_score)
        + 25.0 * worst_score
        + 12.0 * (location.population_factor or 0.0)
        + 8.0 * (location.isolation_factor or 0.0)
    )
    score = round(min(100.0, score), 1)
    level = priority_for_score(score)

    reason = (
        f"Risk score {risk_score:.0f}/100; road status: {road_detail}; "
        f"population factor {location.population_factor:.2f}, "
        f"isolation factor {location.isolation_factor:.2f}. "
        f"{_describe(level)}."
    )

    existing = (
        db.query(EmergencyPriority)
        .filter(EmergencyPriority.location_id == location.id)
        .first()
    )
    if existing is None:
        existing = EmergencyPriority(location_id=location.id)
        db.add(existing)

    existing.priority_level = level
    existing.priority_score = score
    existing.reason = reason
    existing.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.flush()
    return existing


def compute_all_priorities(db: Session) -> list[EmergencyPriority]:
    """Recompute the full emergency ranking.

    Falls back to the latest stored risk score when no risk prediction
    exists for a location yet.
    """
    from ..models import Location, RiskPrediction

    locations = db.query(Location).filter(Location.is_active.is_(True)).all()

    latest: dict[int, float] = {}
    predictions = (
        db.query(RiskPrediction)
        .order_by(RiskPrediction.prediction_time.desc())
        .all()
    )
    for pred in predictions:
        latest.setdefault(pred.location_id, pred.risk_score)

    for loc in locations:
        compute_priority(db, loc, latest.get(loc.id, 0.0))

    return (
        db.query(EmergencyPriority)
        .order_by(EmergencyPriority.priority_score.desc())
        .all()
    )

