from fastapi import APIRouter, Query

from ..ml.risk_engine import (
    RiskFeatures,
    get_risk_engine,
)


router = APIRouter(
    prefix="/ml",
    tags=["Machine Learning"],
)


@router.get("/predict")
def predict(
    latitude: float = Query(...),
    longitude: float = Query(...),
    elevation: float = Query(..., ge=0),
    rainfall: float = Query(..., ge=0),
    soil_moisture: float = Query(..., ge=0, le=100),
    slope_angle: float = Query(..., ge=0, le=90),
    historical_factor: float = Query(0.2, ge=0, le=1),
):
    """
    Predict landslide risk using the hybrid ML risk engine.
    """

    engine = get_risk_engine()

    result = engine.predict(
        RiskFeatures(
            rainfall=rainfall,
            soil_moisture=soil_moisture,
            slope_angle=slope_angle,
            elevation=elevation,
            historical_factor=historical_factor,
        )
    )

    return {
        "latitude": latitude,
        "longitude": longitude,
        **result.as_dict(),
    }