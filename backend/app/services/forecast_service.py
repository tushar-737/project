from ..ml.risk_engine import RiskFeatures, get_risk_engine
from .weather_service import (
    get_forecast_rainfall,
    get_weather_sample,
)


def get_risk_forecast(location) -> dict:
    """
    Predict landslide risk for the next
    24 and 48 hours.
    """

    # Get current real environmental data
    current_sample = get_weather_sample(location)

    # Get forecast rainfall
    rainfall_forecast = get_forecast_rainfall(location)

    engine = get_risk_engine()

    # -----------------------------
    # NEXT 24 HOURS
    # -----------------------------

    risk_24h = engine.predict(
        RiskFeatures(
            rainfall=rainfall_forecast["next_24h"],
            soil_moisture=current_sample.soil_moisture,
            slope_angle=location.slope_angle,
            elevation=location.elevation,
            historical_factor=location.historical_landslide_factor,
            humidity=current_sample.humidity,
            temperature=current_sample.temperature,
        ),
        location=location,
    )

    # -----------------------------
    # NEXT 48 HOURS
    # -----------------------------

    risk_48h = engine.predict(
        RiskFeatures(
            rainfall=rainfall_forecast["next_48h"],
            soil_moisture=current_sample.soil_moisture,
            slope_angle=location.slope_angle,
            elevation=location.elevation,
            historical_factor=location.historical_landslide_factor,
            humidity=current_sample.humidity,
            temperature=current_sample.temperature,
        ),
        location=location,
    )

    return {
        "forecast_rainfall": rainfall_forecast,
        "risk_24h": risk_24h.as_dict(),
        "risk_48h": risk_48h.as_dict(),
    }