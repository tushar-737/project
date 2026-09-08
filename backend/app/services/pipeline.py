"""Automatic risk prediction pipeline.

Whenever new environmental data arrives (simulated or, in the future, from
real IoT sensors) this pipeline runs the complete workflow:

    1. Save environmental data
    2. Run the AI risk engine
    3. Save the risk prediction
    4. Update alert state (create HIGH/CRITICAL alerts)
    5. Dispatch simulated SMS broadcast
    6. Recompute emergency priority for the location
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..ml.risk_engine import RiskFeatures, get_risk_engine
from ..models import EnvironmentalData, RiskPrediction
from .alert_service import process_alert
from .emergency_service import compute_priority


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def run_risk_pipeline(db: Session, location, sample,
                      sample_time: datetime | None = None) -> dict:
    """Execute the full data -> risk -> alert -> priority workflow.

    `sample` is a SensorSample (from services/sensor_service.py) or any
    object with rainfall / soil_moisture / temperature / humidity /
    slope_angle / scenario attributes. Returns a result dict describing
    every pipeline stage; raises on failure so callers can surface errors.
    """
    import json

    steps = ["Environmental data received"]

    # 1. Persist the environmental sample.
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

    # 2. Run the AI risk engine.
    engine = get_risk_engine()
    result = engine.predict(
        RiskFeatures(
            rainfall=env.rainfall,
            soil_moisture=env.soil_moisture,
            slope_angle=env.slope_angle,
            elevation=location.elevation,
            historical_factor=location.historical_landslide_factor,
            humidity=env.humidity,
            temperature=env.temperature,
        ),
        location=location,
    )
    steps.append("AI risk engine executed")

    # 3. Persist the prediction.
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

    # 4. Alert state + simulated SMS.
    alert, is_new, sms = process_alert(db, location, result.score, result.level,
                                       result.factors)
    if is_new:
        steps.append("Alert generated & SMS dispatched")
    elif alert is not None:
        steps.append("Alert already active for this risk level")
    else:
        steps.append("Risk below alert threshold - no alert needed")

    # 5. Emergency priority.
    priority = compute_priority(db, location, result.score)
    steps.append("Emergency priority computed")

    db.commit()

    return {
        "environment": env,
        "prediction": prediction,
        "risk": result,
        "alert": alert,
        "alert_generated": is_new,
        "sms_log": sms,
        "priority": priority,
        "steps": steps,
    }
