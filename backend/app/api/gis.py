from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Location, RiskPrediction
from .deps import get_current_user


router = APIRouter(
    prefix="/gis",
    tags=["GIS"],
)


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
        .filter(Location.is_active == True)
        .all()
    )

    features = []

    for location in locations:

        # Get the latest prediction for this location
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

        # Skip locations that do not yet have a prediction
        if prediction is None:
            continue

        feature = {
            "type": "Feature",

            "geometry": {
                "type": "Point",

                # GeoJSON always uses:
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