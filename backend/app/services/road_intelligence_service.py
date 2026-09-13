from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import Road, Location, RiskPrediction


def utcnow():
    """Return current UTC time without timezone info for SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_road_risk_level(
    risk_score: float,
    risk_level: str,
) -> str:
    """
    Determine the road danger level from the latest
    AI landslide prediction.
    """

    if risk_level == "CRITICAL" or risk_score >= 80:
        return "CRITICAL"

    if risk_level == "HIGH" or risk_score >= 55:
        return "HIGH"

    if risk_level == "MODERATE" or risk_score >= 30:
        return "MODERATE"

    return "LOW"


def get_operational_status(
    risk_score: float,
    risk_level: str,
    current_status: str,
) -> str:
    """
    Determine road operational status.

    IMPORTANT:
    AI can increase restrictions based on danger,
    but it cannot automatically reopen a physically
    blocked or partially blocked road.

    Reopening requires verification by a field officer.
    """

    # =====================================================
    # NEVER AUTOMATICALLY REOPEN DAMAGED ROADS
    # =====================================================

    if current_status == "BLOCKED":
        return "BLOCKED"

    if current_status == "PARTIALLY_BLOCKED":

        # Critical risk can keep the restriction.
        return "PARTIALLY_BLOCKED"

    # =====================================================
    # ROAD IS CURRENTLY OPEN
    # =====================================================

    if risk_level == "CRITICAL" or risk_score >= 80:

        # AI identifies severe danger.
        return "PARTIALLY_BLOCKED"

    # For HIGH / MODERATE / LOW risk,
    # the road remains physically OPEN.
    return "OPEN"
    """
    Determine operational road status.

    IMPORTANT:
    Risk level and operational status are separate.

    HIGH risk does not automatically mean a road is blocked.
    """

    # CRITICAL danger:
    # Keep an already blocked road blocked.
    if risk_level == "CRITICAL" or risk_score >= 80:

        if current_status == "BLOCKED":
            return "BLOCKED"

        return "PARTIALLY_BLOCKED"

    # HIGH danger:
    # Road can remain operational but should be monitored.
    if risk_level == "HIGH" or risk_score >= 55:

        if current_status == "BLOCKED":
            return "BLOCKED"

        if current_status == "PARTIALLY_BLOCKED":
            return "PARTIALLY_BLOCKED"

        return "OPEN"

    # MODERATE danger:
    # Road remains operational.
    if risk_level == "MODERATE" or risk_score >= 30:

        if current_status == "BLOCKED":
            return "BLOCKED"

        return "OPEN"

    # LOW danger:
    # Keep blocked roads unchanged until manually cleared.
    if current_status == "BLOCKED":
        return "BLOCKED"

    return "OPEN"


def update_roads_from_risk(
    db: Session,
    location,
    risk_score: float,
    risk_level: str,
):
    """
    Update roads linked to one monitored location.

    The AI prediction updates the road risk level.

    Operational status is handled separately because
    a dangerous area does not automatically mean that
    the physical road is blocked.

    Every evaluation updates updated_at.
    """

    roads = (
        db.query(Road)
        .filter(Road.location_id == location.id)
        .all()
    )

    updated_roads = []

    for road in roads:

        old_status = road.status
        old_risk_level = road.risk_level

        new_risk_level = get_road_risk_level(
            risk_score,
            risk_level,
        )

        new_status = get_operational_status(
            risk_score,
            risk_level,
            road.status,
        )

        status_changed = old_status != new_status

        risk_changed = (
            old_risk_level != new_risk_level
        )

        # Update road intelligence.
        road.status = new_status
        road.risk_level = new_risk_level

        # Every AI evaluation gets a fresh timestamp.
        road.updated_at = utcnow()

        if status_changed or risk_changed:

            updated_roads.append(
                {
                    "id": road.id,
                    "name": road.name,
                    "old_status": old_status,
                    "new_status": new_status,
                    "old_risk_level": old_risk_level,
                    "new_risk_level": new_risk_level,
                }
            )

    db.flush()

    return updated_roads


def refresh_all_road_intelligence(
    db: Session,
):
    """
    Re-evaluate all monitored roads using the latest
    available AI risk prediction for every active location.

    This does NOT generate fake environmental data.

    It only uses the latest prediction already stored
    in the database.
    """

    locations = (
        db.query(Location)
        .filter(Location.is_active.is_(True))
        .all()
    )

    total_locations = 0
    total_roads = 0
    changed_roads = []

    for location in locations:

        total_locations += 1

        latest_prediction = (
            db.query(RiskPrediction)
            .filter(
                RiskPrediction.location_id
                == location.id
            )
            .order_by(
                RiskPrediction.prediction_time.desc()
            )
            .first()
        )

        # Skip locations that have no prediction yet.
        if latest_prediction is None:
            continue

        roads = (
            db.query(Road)
            .filter(
                Road.location_id == location.id
            )
            .all()
        )

        total_roads += len(roads)

        updates = update_roads_from_risk(
            db=db,
            location=location,
            risk_score=latest_prediction.risk_score,
            risk_level=latest_prediction.risk_level,
        )

        changed_roads.extend(updates)

    db.commit()

    return {
        "locations_checked": total_locations,
        "roads_evaluated": total_roads,
        "roads_changed": len(changed_roads),
        "changes": changed_roads,
        "refreshed_at": utcnow(),
    }