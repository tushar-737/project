from sqlalchemy.orm import Session

from ..models import Location, RiskPrediction


def get_risk_heatmap_data(
    db: Session,
) -> list[dict]:
    """
    Generate GIS-ready risk heatmap data.

    Each monitored location returns:

    - Latitude
    - Longitude
    - Risk score
    - Risk level
    - Location information

    The latest prediction for each active
    location is used.
    """

    locations = (
        db.query(Location)
        .filter(Location.is_active.is_(True))
        .all()
    )

    heatmap_points = []

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

        # Skip locations that have not yet
        # received an AI prediction.
        if latest_prediction is None:
            continue

        heatmap_points.append(
            {
                "location_id": location.id,

                "latitude": location.latitude,

                "longitude": location.longitude,

                "risk_score": latest_prediction.risk_score,

                "risk_level": latest_prediction.risk_level,

                "confidence": latest_prediction.confidence,

                "location_name": location.name,

                "district": location.district,

                "state": location.state,

                "prediction_time": (
                    latest_prediction.prediction_time
                ),
            }
        )

    return heatmap_points


def get_heatmap_summary(
    db: Session,
) -> dict:
    """
    Generate summary statistics for the GIS
    risk heatmap.
    """

    points = get_risk_heatmap_data(db)

    summary = {
        "total_locations": len(points),

        "low": 0,

        "moderate": 0,

        "high": 0,

        "critical": 0,

    }

    for point in points:

        risk_level = (
            point["risk_level"]
            .lower()
        )

        if risk_level in summary:

            summary[risk_level] += 1

    return {

        "summary": summary,

        "points": points,

    }