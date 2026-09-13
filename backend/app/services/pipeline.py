from datetime import datetime, timezone
import json

from sqlalchemy.orm import Session

from ..ml.risk_engine import RiskFeatures, get_risk_engine
from ..models import (
    EnvironmentalData,
    RiskPrediction,
    SatelliteObservation,
)

from .alert_service import process_alert
from .emergency_service import compute_priority
from .road_intelligence_service import update_roads_from_risk
from .satellite_service import get_satellite_intelligence


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def run_risk_pipeline(
    db: Session,
    location,
    sample,
    sample_time: datetime | None = None,
) -> dict:

    steps = ["Environmental data received"]

    # ========================================================
    # SAVE ENVIRONMENTAL DATA
    # ========================================================

    env = EnvironmentalData(
        location_id=location.id,
        rainfall=round(sample.rainfall, 1),
        soil_moisture=round(sample.soil_moisture, 1),
        temperature=round(sample.temperature, 1),
        humidity=round(sample.humidity, 1),
        slope_angle=round(sample.slope_angle, 1),
        scenario=sample.scenario,
        timestamp=sample_time or utcnow(),
    )

    db.add(env)
    db.flush()

    steps.append("Environmental data saved")

    # ========================================================
    # AI / ML RISK ENGINE
    # ========================================================

    engine = get_risk_engine()

    result = engine.predict(
        RiskFeatures(
            # Current rainfall from the previous 24 hours.
            rainfall=env.rainfall,

            # Antecedent rainfall from Open-Meteo.
            rainfall_72h=getattr(sample, "rainfall_72h", 0.0),
            rainfall_7d=getattr(sample, "rainfall_7d", 0.0),

            # Current environmental conditions.
            soil_moisture=env.soil_moisture,
            humidity=env.humidity,
            temperature=env.temperature,

            # Terrain information.
            slope_angle=env.slope_angle,
            elevation=location.elevation,

            # Historical landslide information.
            historical_factor=location.historical_landslide_factor,
        ),
        location=location,
    )

    steps.append("AI risk engine executed")

    # ========================================================
    # SATELLITE INTELLIGENCE
    # ========================================================

    satellite = get_satellite_intelligence(
        location=location,
        rainfall_24h=env.rainfall,
        rainfall_72h=getattr(sample, "rainfall_72h", 0.0),
        soil_moisture=env.soil_moisture,
    )

    steps.append(
        f"Satellite intelligence analysed: {satellite.status}"
    )

    # ========================================================
    # SAVE SATELLITE OBSERVATION
    # ========================================================

    satellite_observation = SatelliteObservation(
        location_id=location.id,
        vegetation_index=satellite.vegetation_index,
        surface_wetness=satellite.surface_wetness,
        vegetation_risk=satellite.vegetation_risk,
        wetness_risk=satellite.wetness_risk,
        satellite_risk=satellite.satellite_risk,
        status=satellite.status,
        source=satellite.source,
        observation_time=env.timestamp,
    )

    db.add(satellite_observation)
    db.flush()

    steps.append("Satellite observation saved")

    # ========================================================
    # SAVE RISK PREDICTION
    # ========================================================

    prediction = RiskPrediction(
        location_id=location.id,
        risk_score=result.score,
        risk_level=result.level,
        confidence=result.confidence,
        contributing_factors=json.dumps(result.factors),
        prediction_time=env.timestamp,
    )

    db.add(prediction)
    db.flush()

    steps.append("Risk prediction saved")

    # ========================================================
    # ROAD INTELLIGENCE
    # ========================================================

    updated_roads = update_roads_from_risk(
        db=db,
        location=location,
        risk_score=result.score,
        risk_level=result.level,
    )

    if updated_roads:

        road_names = ", ".join(
            f"{road['name']} "
            f"({road['old_status']} → {road['new_status']})"
            for road in updated_roads
        )

        steps.append(
            f"Road connectivity updated: {road_names}"
        )

    else:

        steps.append(
            "Road connectivity checked - no status change"
        )

    # ========================================================
    # ALERT PROCESSING
    # ========================================================

    alert, is_new, sms = process_alert(
        db,
        location,
        result.score,
        result.level,
        result.factors,
    )

    if is_new:

        steps.append(
            "Alert generated and SMS dispatched"
        )

    elif alert is not None:

        steps.append(
            "Alert already active for this risk level"
        )

    else:

        steps.append(
            "Risk below alert threshold - no alert needed"
        )

    # ========================================================
    # EMERGENCY PRIORITY
    # ========================================================

    priority = compute_priority(
        db,
        location,
        result.score,
    )

    steps.append(
        f"Emergency priority computed: "
        f"{priority.priority_level}"
    )

    # ========================================================
    # COMMIT DATABASE
    # ========================================================

    db.commit()

    # ========================================================
    # RETURN PIPELINE RESULT
    # ========================================================

    return {
        "environment": env,
        "prediction": prediction,
        "risk": result,

        "satellite": satellite,
        "satellite_observation": satellite_observation,

        "alert": alert,
        "alert_generated": is_new,
        "sms_log": sms,

        "priority": priority,

        "updated_roads": updated_roads,

        "steps": steps,
    }