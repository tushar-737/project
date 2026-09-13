from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Location, RiskPrediction

from ..services.gis_heatmap_service import (
    get_heatmap_summary,
    get_risk_heatmap_data,
)

from .deps import get_current_user


router = APIRouter(
    prefix="/gis",
    tags=["GIS"],
)


# ==========================================================
# GEOJSON RISK MAP
# ==========================================================

@router.get("/risk-map")
def get_risk_map(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    Return the latest risk prediction for every
    active monitored location in GeoJSON format.
    """

    locations = (
        db.query(Location)
        .filter(Location.is_active.is_(True))
        .all()
    )

    features = []

    for location in locations:

        # Get the latest prediction
        prediction = (
            db.query(RiskPrediction)
            .filter(
                RiskPrediction.location_id == location.id
            )
            .order_by(
                RiskPrediction.prediction_time.desc()
            )
            .first()
        )

        # Skip locations without predictions
        if prediction is None:
            continue

        feature = {
            "type": "Feature",

            "geometry": {
                "type": "Point",

                # GeoJSON format:
                # [longitude, latitude]
                "coordinates": [
                    location.longitude,
                    location.latitude,
                ],
            },

            "properties": {
                "location_id": location.id,

                "name": location.name,

                "district": location.district,

                "state": location.state,

                "elevation": location.elevation,

                "slope_angle": location.slope_angle,

                "risk_score": prediction.risk_score,

                "risk_level": prediction.risk_level,

                "confidence": prediction.confidence,

                "prediction_time": (
                    prediction.prediction_time.isoformat()
                ),
            },
        }

        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }


# ==========================================================
# GIS HEATMAP DATA
# ==========================================================

@router.get("/heatmap")
def get_heatmap(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    Return GIS-ready landslide risk heatmap points.

    Designed for frontend map libraries such as:

    - Leaflet
    - React Leaflet
    - Mapbox
    - GIS dashboards
    """

    points = get_risk_heatmap_data(
        db=db,
    )

    return {
        "total_points": len(points),
        "points": points,
    }


# ==========================================================
# HEATMAP SUMMARY
# ==========================================================

@router.get("/heatmap/summary")
def get_heatmap_statistics(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    Return risk distribution and GIS heatmap
    summary statistics.
    """

    return get_heatmap_summary(
        db=db,
    )