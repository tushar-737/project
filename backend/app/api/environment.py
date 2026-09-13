"""
Environment telemetry endpoints.

Supports:

1. IoT / hardware readings
   POST /api/environment/ingest

2. Live weather for one monitored location
   POST /api/environment/fetch-live-weather/{location_id}

3. Live weather refresh for all monitored NER locations
   POST /api/environment/refresh-all-live-weather

4. Landslide risk forecast
   GET /api/environment/forecast/{location_id}
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

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


router = APIRouter(
    prefix="/environment",
    tags=["environment"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class IngestSample(BaseModel):
    location_id: int

    rainfall: float = Field(ge=0, le=1000)
    soil_moisture: float = Field(ge=0, le=100)
    temperature: float = Field(ge=-20, le=60)
    humidity: float = Field(ge=0, le=100)
    slope_angle: float = Field(ge=0, le=90)


# ============================================================
# ENVIRONMENT HISTORY
# ============================================================

@router.get("/{location_id}")
def environment_history(
    location_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get telemetry history for one monitored location."""

    location = db.get(Location, location_id)

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    rows = (
        db.query(EnvironmentalData)
        .filter(
            EnvironmentalData.location_id == location_id
        )
        .order_by(
            EnvironmentalData.timestamp.desc()
        )
        .limit(limit)
        .all()
    )

    return [
        EnvironmentalDataOut.model_validate(row)
        for row in rows
    ]


# ============================================================
# IOT / HARDWARE DATA INGESTION
# ============================================================

@router.post("/ingest")
def ingest_sensor_reading(
    payload: IngestSample,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    Receive a real IoT / hardware sensor reading.

    Future sensors can send:

    - rainfall
    - soil moisture
    - temperature
    - humidity
    - slope angle

    The reading goes through the same
    automatic landslide risk pipeline.
    """

    location = db.get(
        Location,
        payload.location_id,
    )

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    class _Sample:

        scenario = "REAL_IOT"

        def __init__(
            self,
            reading: IngestSample,
        ):
            self.rainfall = reading.rainfall
            self.soil_moisture = (
                reading.soil_moisture
            )
            self.temperature = (
                reading.temperature
            )
            self.humidity = reading.humidity
            self.slope_angle = (
                reading.slope_angle
            )

    result = run_risk_pipeline(
        db,
        location,
        _Sample(payload),
    )

    return {
        "source": "REAL_IOT",

        "location": {
            "id": location.id,
            "name": location.name,
            "latitude": location.latitude,
            "longitude": location.longitude,
        },

        "environment": (
            EnvironmentalDataOut.model_validate(
                result["environment"]
            )
        ),

        "risk": result["risk"].as_dict(),

        "alert_generated": (
            result["alert_generated"]
        ),

        "priority_level": (
            result["priority"].priority_level
            if result["priority"]
            else None
        ),

        "steps": result["steps"],
    }


# ============================================================
# LIVE WEATHER - ONE LOCATION
# ============================================================

@router.post(
    "/fetch-live-weather/{location_id}"
)
def fetch_live_weather(
    location_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    Fetch real weather data for one location
    and run the landslide risk pipeline.
    """

    location = db.get(
        Location,
        location_id,
    )

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    try:

        sample = get_weather_sample(
            location
        )

        result = run_risk_pipeline(
            db,
            location,
            sample,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to fetch live weather data: "
                f"{str(exc)}"
            ),
        )

    return {
        "source": "OPEN_METEO",

        "location": {
            "id": location.id,
            "name": location.name,
            "latitude": location.latitude,
            "longitude": location.longitude,
        },

        "environment": (
            EnvironmentalDataOut.model_validate(
                result["environment"]
            )
        ),

        "risk": result["risk"].as_dict(),

        "alert_generated": (
            result["alert_generated"]
        ),

        "priority_level": (
            result["priority"].priority_level
            if result["priority"]
            else None
        ),

        "steps": result["steps"],
    }


# ============================================================
# LIVE WEATHER - ALL NER LOCATIONS
# ============================================================

@router.post(
    "/refresh-all-live-weather"
)
def refresh_all_live_weather(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    Refresh live weather for all monitored
    locations.

    Weather API requests are fetched
    concurrently for better performance.

    Database operations remain in the main
    thread because SQLAlchemy sessions
    should not be shared between threads.
    """

    locations = (
        db.query(Location)
        .order_by(Location.id)
        .all()
    )

    if not locations:
        raise HTTPException(
            status_code=404,
            detail="No monitored locations found",
        )

    processed_locations = []
    failed_locations = []

    risk_counts = {
        "LOW": 0,
        "MODERATE": 0,
        "HIGH": 0,
        "CRITICAL": 0,
    }

    alerts_generated = 0


    # ========================================================
    # STEP 1: FETCH WEATHER CONCURRENTLY
    # ========================================================

    weather_results = {}


    def fetch_weather(location):

        sample = get_weather_sample(
            location
        )

        return (
            location.id,
            sample,
        )


    with ThreadPoolExecutor(
        max_workers=10
    ) as executor:

        future_to_location = {

            executor.submit(
                fetch_weather,
                location,
            ): location

            for location in locations

        }


        for future in as_completed(
            future_to_location
        ):

            location = (
                future_to_location[future]
            )

            try:

                location_id, sample = (
                    future.result()
                )

                weather_results[
                    location_id
                ] = sample


            except Exception as exc:

                failed_locations.append({

                    "id": location.id,

                    "name": location.name,

                    "state": location.state,

                    "error": str(exc),

                })


    # ========================================================
    # STEP 2: RUN AI PIPELINE
    # ========================================================

    for location in locations:

        if location.id not in weather_results:
            continue


        try:

            sample = weather_results[
                location.id
            ]


            result = run_risk_pipeline(

                db,

                location,

                sample,

            )


            risk = result["risk"]

            risk_level = risk.level


            # Count risk levels

            if risk_level in risk_counts:

                risk_counts[
                    risk_level
                ] += 1


            # Count alerts

            if result["alert_generated"]:

                alerts_generated += 1


            # Store location summary

            processed_locations.append({

                "id": location.id,

                "name": location.name,

                "district": location.district,

                "state": location.state,

                "latitude": location.latitude,

                "longitude": location.longitude,


                "rainfall": (
                    result["environment"].rainfall
                ),

                "temperature": (
                    result["environment"].temperature
                ),

                "humidity": (
                    result["environment"].humidity
                ),

                "soil_moisture": (
                    result["environment"]
                    .soil_moisture
                ),


                "risk_score": (
                    risk.score
                ),

                "risk_level": (
                    risk_level
                ),

                "confidence": (
                    risk.confidence
                ),


                "alert_generated": (
                    result["alert_generated"]
                ),


                "priority_level": (

                    result["priority"].priority_level

                    if result["priority"]

                    else None

                ),

            })


        except Exception as exc:

            failed_locations.append({

                "id": location.id,

                "name": location.name,

                "state": location.state,

                "error": str(exc),

            })


    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {

        "source": "OPEN_METEO",

        "region": (
            "North Eastern Region of India"
        ),

        "timestamp": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),

        "total_locations": (
            len(locations)
        ),

        "locations_processed": (
            len(processed_locations)
        ),

        "locations_failed": (
            len(failed_locations)
        ),


        "risk_summary": {

            "LOW": (
                risk_counts["LOW"]
            ),

            "MODERATE": (
                risk_counts["MODERATE"]
            ),

            "HIGH": (
                risk_counts["HIGH"]
            ),

            "CRITICAL": (
                risk_counts["CRITICAL"]
            ),

        },


        "alerts_generated": (
            alerts_generated
        ),


        "processed_locations": (
            processed_locations
        ),


        "failed_locations": (
            failed_locations
        ),


        "pipeline": [

            "Live weather data fetched",

            "Environmental data saved",

            "AI risk engine executed",

            "Risk prediction saved",

            "Alert decision executed",

            "Emergency priority computed",

        ],

    }


# ============================================================
# LANDSLIDE RISK FORECAST
# ============================================================

@router.get(
    "/forecast/{location_id}"
)
def get_forecast(
    location_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    Get 24-hour and 48-hour
    landslide risk forecasts.
    """

    location = db.get(
        Location,
        location_id,
    )

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    try:

        forecast = get_risk_forecast(
            location
        )

        return {

            "location": {

                "id": location.id,

                "name": location.name,

                "latitude": (
                    location.latitude
                ),

                "longitude": (
                    location.longitude
                ),

            },

            **forecast,

        }


    except Exception as exc:

        raise HTTPException(

            status_code=502,

            detail=(

                "Unable to generate forecast: "

                f"{str(exc)}"

            ),

        )