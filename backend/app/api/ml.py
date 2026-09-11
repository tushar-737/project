from fastapi import APIRouter

from ..ml.risk_model import predict_landslide_risk


router = APIRouter(
    prefix="/ml",
    tags=["Machine Learning"],
)


@router.get("/predict")
def predict(
    rainfall: float,
    soil_moisture: float,
    slope_angle: float,
):
    """
    Predict landslide risk using environmental parameters.
    """

    result = predict_landslide_risk(
        rainfall=rainfall,
        soil_moisture=soil_moisture,
        slope_angle=slope_angle,
    )

    return result