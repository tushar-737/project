from sqlalchemy.orm import Session

from ..models import Location, RiskPrediction


def get_high_risk_zones(
    db: Session,
    minimum_score: float = 50.0,
) -> list[dict]:
    """
    Return monitored locations with their latest
    landslide risk prediction.

    The output is GIS/dashboard ready.
    """

    locations = (
        db.query(Location)
        .filter(Location.is_active.is_(True))
        .all()
    )

    zones = []

    for location in locations:

        latest_prediction = (
            db.query(RiskPrediction)
            .filter(
                RiskPrediction.location_id == location.id
            )
            .order_by(
                RiskPrediction.prediction_time.desc()
            )
            .first()
        )

        if latest_prediction is None:
            continue

        if latest_prediction.risk_score < minimum_score:
            continue

        zones.append(
            {
                "location_id": location.id,

                "name": location.name,

                "district": location.district,

                "state": location.state,

                "latitude": location.latitude,

                "longitude": location.longitude,

                "elevation": location.elevation,

                "slope_angle": location.slope_angle,

                "risk_score": latest_prediction.risk_score,

                "risk_level": latest_prediction.risk_level,

                "confidence": latest_prediction.confidence,

                "prediction_time": (
                    latest_prediction.prediction_time
                ),
            }
        )

    zones.sort(
        key=lambda zone: zone["risk_score"],
        reverse=True,
    )

    return zones


def get_all_risk_zones(
    db: Session,
) -> list[dict]:
    """
    Return all active monitored locations with
    their latest risk prediction.

    Useful for GIS maps and risk heatmaps.
    """

    return get_high_risk_zones(
        db=db,
        minimum_score=0,
    )