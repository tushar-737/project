"""Risk endpoints: zones, detail, history and the aggregate trend.

IMPORTANT: literal routes (/zones, /zones/summary, /trend/overview)
are declared BEFORE the parameterised /{location_id} routes so FastAPI
never tries to parse a word like "trend" as an integer.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Location, RiskPrediction
from ..ml.risk_model import predict_landslide_risk
from ..schemas.environment import EnvironmentalDataOut
from ..schemas.location import LocationOut
from ..schemas.risk import RiskPredictionOut

from ..utils.queries import (
    latest_environment_by_location,
    latest_risk_by_location,
)

from ..services.alert_service import process_alert
from ..services.emergency_service import compute_priority


router = APIRouter(prefix="/risk", tags=["risk"])


# ==========================================================
# RISK ZONES
# ==========================================================

def _build_zones(
    db: Session,
    state: str | None,
    level: str | None,
) -> list[dict]:

    query = db.query(Location).filter(
        Location.is_active.is_(True)
    )

    if state:
        query = query.filter(
            Location.state == state
        )

    locations = query.order_by(
        Location.state,
        Location.name,
    ).all()

    env_map = latest_environment_by_location(db)
    risk_map = latest_risk_by_location(db)

    zones = []

    for loc in locations:

        pred = risk_map.get(loc.id)

        if level and (
            not pred
            or pred.risk_level != level.upper()
        ):
            continue

        env = env_map.get(loc.id)

        zones.append({
            "location_id": loc.id,
            "name": loc.name,
            "district": loc.district,
            "state": loc.state,

            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "elevation": loc.elevation,

            "historical_landslide_factor":
                loc.historical_landslide_factor,

            "population_factor":
                loc.population_factor,

            "isolation_factor":
                loc.isolation_factor,

            "risk_score":
                pred.risk_score if pred else 0.0,

            "risk_level":
                pred.risk_level if pred else "LOW",

            "confidence":
                pred.confidence if pred else 0.0,

            "rainfall":
                env.rainfall if env else None,

            "soil_moisture":
                env.soil_moisture if env else None,

            "humidity":
                env.humidity if env else None,

            "slope_angle":
                env.slope_angle
                if env
                else loc.slope_angle,

            "temperature":
                env.temperature if env else None,

            "scenario":
                env.scenario if env else None,

            "prediction_time":
                pred.prediction_time if pred else None,

            "last_updated":
                env.timestamp if env else None,
        })

    zones.sort(
        key=lambda z: z["risk_score"],
        reverse=True,
    )

    return zones


# ==========================================================
# GET ALL RISK ZONES
# ==========================================================

@router.get("/zones")
def risk_zones(

    state: str | None = Query(
        default=None
    ),

    level: str | None = Query(
        default=None
    ),

    db: Session = Depends(get_db),

):
    """Current risk overview for every active location."""

    return _build_zones(
        db,
        state,
        level,
    )


# ==========================================================
# RISK ZONE SUMMARY
# ==========================================================

@router.get("/zones/summary")
def risk_zone_summary(
    db: Session = Depends(get_db),
):
    """Counts per risk level."""

    zones = _build_zones(
        db,
        None,
        None,
    )

    summary = {
        "low": 0,
        "moderate": 0,
        "high": 0,
        "critical": 0,
        "total": len(zones),
    }

    for zone in zones:

        key = zone["risk_level"].lower()

        if key in summary:
            summary[key] += 1

    return summary


# ==========================================================
# AGGREGATE RISK TREND
# ==========================================================

@router.get("/trend/overview")
def risk_trend(
    db: Session = Depends(get_db),
):
    """Aggregated recent risk across all locations."""

    latest = (
        db.query(RiskPrediction)
        .order_by(
            RiskPrediction.prediction_time.desc()
        )
        .first()
    )

    cutoff = (
        latest.prediction_time
        - timedelta(hours=72)
        if latest
        else None
    )

    rows = (
        db.query(RiskPrediction)
        .order_by(
            RiskPrediction.prediction_time.asc()
        )
        .all()
    )

    if cutoff:

        rows = [
            row
            for row in rows
            if row.prediction_time >= cutoff
        ]

    buckets: dict[str, list[float]] = {}

    for row in rows:

        key = row.prediction_time.strftime(
            "%Y-%m-%dT%H:00:00"
        )

        buckets.setdefault(
            key,
            [],
        ).append(
            row.risk_score
        )

    return [

        {
            "time": key,

            "avg_score": round(
                sum(values) / len(values),
                1,
            ),

            "samples": len(values),

            "max_score": round(
                max(values),
                1,
            ),
        }

        for key, values in sorted(
            buckets.items()
        )

    ]


# ==========================================================
# PREDICT ONE LOCATION
# ==========================================================

@router.post("/{location_id}/predict")
def predict_location_risk(

    location_id: int,

    db: Session = Depends(get_db),

):
    """
    Run the ML risk engine using the latest
    environmental data for one location.

    Pipeline:

    Environmental Data
            ↓
    ML Risk Prediction
            ↓
    Alert Engine
            ↓
    SMS Warning
            ↓
    Emergency Priority
    """

    # ------------------------------------------------------
    # GET LOCATION
    # ------------------------------------------------------

    location = db.get(
        Location,
        location_id,
    )

    if not location:

        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    # ------------------------------------------------------
    # GET LATEST ENVIRONMENTAL DATA
    # ------------------------------------------------------

    env_map = latest_environment_by_location(
        db
    )

    env = env_map.get(
        location_id
    )

    if not env:

        raise HTTPException(
            status_code=404,
            detail=(
                "No environmental data available "
                "for this location"
            ),
        )

    # ------------------------------------------------------
    # RUN ML MODEL
    # ------------------------------------------------------

    result = predict_landslide_risk(

        rainfall=env.rainfall or 0,

        soil_moisture=(
            env.soil_moisture or 0
        ),

        slope_angle=(
            env.slope_angle
            or location.slope_angle
            or 0
        ),

    )

    # ------------------------------------------------------
    # SAVE RISK PREDICTION
    # ------------------------------------------------------

    prediction = RiskPrediction(

        location_id=location.id,

        risk_score=result["risk_score"],

        risk_level=result["risk_level"],

        confidence=result["confidence"],

        contributing_factors=str(
            result["contributing_factors"]
        ),

    )

    db.add(prediction)

    # Make prediction available inside
    # the current transaction.
    db.flush()

    # ------------------------------------------------------
    # EARLY WARNING ALERT PIPELINE
    # ------------------------------------------------------

    alert, alert_generated, sms = process_alert(

        db=db,

        location=location,

        risk_score=result["risk_score"],

        risk_level=result["risk_level"],

        factors=result["contributing_factors"],

    )

    # ------------------------------------------------------
    # EMERGENCY RESPONSE PRIORITY
    # ------------------------------------------------------

    priority = compute_priority(

        db=db,

        location=location,

        risk_score=result["risk_score"],

    )

    # ------------------------------------------------------
    # COMMIT EVERYTHING
    # ------------------------------------------------------

    db.commit()

    db.refresh(prediction)

    # ------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------

    return {

        "location": location.name,

        "location_id": location.id,

        "prediction":
            RiskPredictionOut.from_row(
                prediction
            ),

        "alert_generated":
            alert_generated,

        "alert": (

            {
                "id": alert.id,
                "risk_level":
                    alert.risk_level,
                "status":
                    alert.status,
            }

            if alert
            else None

        ),

        "sms": (

            {
                "id": sms.id,

                "recipient_area":
                    sms.recipient_area,

                "phone_recipients":
                    sms.phone_recipients,

                "channel":
                    sms.channel,

                "status":
                    sms.status,
            }

            if sms
            else None

        ),

        "emergency_priority": {

            "priority_level":
                priority.priority_level,

            "priority_score":
                priority.priority_score,

            "reason":
                priority.reason,

        },

    }


# ==========================================================
# PREDICT ALL LOCATIONS
# ==========================================================

@router.post("/predict-all")
def predict_all_locations(

    db: Session = Depends(get_db),

):
    """
    Run the complete prediction pipeline
    for all active locations.

    Pipeline:

    ML Prediction
        ↓
    Alert Generation
        ↓
    SMS Warning
        ↓
    Emergency Priority
    """

    locations = (

        db.query(Location)

        .filter(
            Location.is_active.is_(True)
        )

        .all()

    )

    env_map = latest_environment_by_location(
        db
    )

    results = []

    skipped = []

    alerts_generated = 0

    sms_sent = 0


    # ------------------------------------------------------
    # PROCESS EACH LOCATION
    # ------------------------------------------------------

    for location in locations:

        env = env_map.get(
            location.id
        )

        # Skip locations with no environmental data.

        if not env:

            skipped.append({

                "location_id":
                    location.id,

                "name":
                    location.name,

                "reason":
                    "No environmental data",

            })

            continue


        # --------------------------------------------------
        # RUN ML MODEL
        # --------------------------------------------------

        result = predict_landslide_risk(

            rainfall=env.rainfall or 0,

            soil_moisture=(
                env.soil_moisture or 0
            ),

            slope_angle=(

                env.slope_angle
                or location.slope_angle
                or 0

            ),

        )


        # --------------------------------------------------
        # SAVE PREDICTION
        # --------------------------------------------------

        prediction = RiskPrediction(

            location_id=location.id,

            risk_score=result["risk_score"],

            risk_level=result["risk_level"],

            confidence=result["confidence"],

            contributing_factors=str(

                result[
                    "contributing_factors"
                ]

            ),

        )

        db.add(prediction)

        db.flush()


        # --------------------------------------------------
        # PROCESS ALERT
        # --------------------------------------------------

        alert, alert_generated, sms = process_alert(

            db=db,

            location=location,

            risk_score=result["risk_score"],

            risk_level=result["risk_level"],

            factors=result[
                "contributing_factors"
            ],

        )


        if alert_generated:

            alerts_generated += 1


        if sms:

            sms_sent += 1


        # --------------------------------------------------
        # EMERGENCY PRIORITY
        # --------------------------------------------------

        priority = compute_priority(

            db=db,

            location=location,

            risk_score=result[
                "risk_score"
            ],

        )


        # --------------------------------------------------
        # STORE RESULT
        # --------------------------------------------------

        results.append({

            "location_id":
                location.id,

            "location":
                location.name,

            "risk_score":
                result["risk_score"],

            "risk_level":
                result["risk_level"],

            "alert_generated":
                alert_generated,

            "sms_sent":
                sms is not None,

            "priority_level":
                priority.priority_level,

            "priority_score":
                priority.priority_score,

        })


    # ------------------------------------------------------
    # SAVE EVERYTHING
    # ------------------------------------------------------

    db.commit()


    return {

        "message":
            "Complete landslide prediction pipeline completed",

        "locations_processed":
            len(results),

        "locations_skipped":
            len(skipped),

        "alerts_generated":
            alerts_generated,

        "sms_sent":
            sms_sent,

        "predictions":
            results,

        "skipped":
            skipped,

    }


# ==========================================================
# RISK HISTORY
# ==========================================================

@router.get("/{location_id}/history")
def risk_history(

    location_id: int,

    limit: int = Query(
        default=50,
        ge=1,
        le=500,
    ),

    db: Session = Depends(get_db),

):
    """Time series of past predictions."""

    if not db.get(
        Location,
        location_id,
    ):

        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    rows = (

        db.query(RiskPrediction)

        .filter(
            RiskPrediction.location_id
            == location_id
        )

        .order_by(
            RiskPrediction.prediction_time.desc()
        )

        .limit(limit)

        .all()

    )

    rows.reverse()

    return [

        RiskPredictionOut.from_row(row)

        for row in rows

    ]


# ==========================================================
# RISK DETAIL
# ==========================================================

@router.get("/{location_id}")
def risk_detail(

    location_id: int,

    db: Session = Depends(get_db),

):
    """
    Location + latest environmental data
    + latest risk prediction.
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

    env = (

        latest_environment_by_location(
            db
        )

        .get(location_id)

    )

    pred = (

        latest_risk_by_location(
            db
        )

        .get(location_id)

    )


    return {

        "location":

            LocationOut.model_validate(
                location
            ),

        "environment":

            EnvironmentalDataOut.model_validate(
                env
            )

            if env

            else None,

        "risk":

            RiskPredictionOut.from_row(
                pred
            )

            if pred

            else None,

    }