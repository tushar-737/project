"""Environment telemetry endpoints (simulated samples today).

POST /api/environment/ingest is the endpoint future real IoT gateways use
to push hardware readings - it feeds the exact same automatic pipeline as
the simulator.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import EnvironmentalData, Location
from ..schemas.environment import EnvironmentalDataOut
from .deps import get_current_user
from ..services.pipeline import run_risk_pipeline
from ..services.weather_service import get_weather_sample
from ..services.forecast_service import get_risk_forecast

router = APIRouter(prefix="/environment", tags=["environment"])


class IngestSample(BaseModel):
    location_id: int
    rainfall: float = Field(ge=0, le=1000)
    soil_moisture: float = Field(ge=0, le=100)
    temperature: float = Field(ge=-20, le=60)
    humidity: float = Field(ge=0, le=100)
    slope_angle: float = Field(ge=0, le=90)


@router.get("/{location_id}")
def environment_history(
    location_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Telemetry history for one location, newest first."""
    location = db.get(Location, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    rows = (
        db.query(EnvironmentalData)
        .filter(EnvironmentalData.location_id == location_id)
        .order_by(EnvironmentalData.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [EnvironmentalDataOut.model_validate(r) for r in rows]


@router.post("/ingest")
def ingest_sensor_reading(
    payload: IngestSample,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Receives a hardware/simulator reading and runs the risk pipeline.

    Returns the same payload shape as a simulation run so gateways see the
    resulting risk level, alert and priority in one response.
    """
    location = db.get(Location, payload.location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    class _Sample:
        scenario = "REAL_IOT"

        def __init__(self, p: IngestSample):
            self.rainfall = p.rainfall
            self.soil_moisture = p.soil_moisture
            self.temperature = p.temperature
            self.humidity = p.humidity
            self.slope_angle = p.slope_angle

    result = run_risk_pipeline(db, location, _Sample(payload))
    return {
        "environment": EnvironmentalDataOut.model_validate(result["environment"]),
        "risk": result["risk"].as_dict(),
        "alert_generated": result["alert_generated"],
        "priority_level": result["priority"].priority_level if result["priority"] else None,
    }
@router.post("/fetch-live-weather/{location_id}")
def fetch_live_weather(
    location_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    Fetch real weather data for a location and run
    the existing landslide risk prediction pipeline.
    """

    location = db.get(Location, location_id)

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    try:
        # Fetch real weather data using location coordinates
        sample = get_weather_sample(location)

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to fetch live weather data: {str(exc)}",
        )

    # Run the existing complete pipeline
    result = run_risk_pipeline(
        db,
        location,
        sample,
    )

    return {
        "source": "OPEN_METEO",
        "location": {
            "id": location.id,
            "name": location.name,
            "latitude": location.latitude,
            "longitude": location.longitude,
        },
        "environment": EnvironmentalDataOut.model_validate(
            result["environment"]
        ),
        "risk": result["risk"].as_dict(),
        "alert_generated": result["alert_generated"],
        "priority_level": (
            result["priority"].priority_level
            if result["priority"]
            else None
        ),
        "steps": result["steps"],
    }
@router.get("/forecast/{location_id}")
def get_forecast(
    location_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    Get 24-hour and 48-hour
    landslide risk forecasts.
    """

    location = db.get(Location, location_id)

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    try:
        forecast = get_risk_forecast(location)

        return {
            "location": {
                "id": location.id,
                "name": location.name,
                "latitude": location.latitude,
                "longitude": location.longitude,
            },
            **forecast,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to generate forecast: {str(exc)}",
        )