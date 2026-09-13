from datetime import datetime, timezone
import json

from sqlalchemy.orm import Session

from ..ml.risk_engine import RiskFeatures, get_risk_engine
from ..models import EnvironmentalData, RiskPrediction
from .alert_service import process_alert
from .emergency_service import compute_priority
from .road_intelligence_service import update_roads_from_risk


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def run_risk_pipeline(
    db: Session,
    location,
    sample,
    sample_time: datetime | None = None,
) -> dict:
    steps = ["Environmental data received"]

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

    updated_roads = update_roads_from_risk(
        db=db,
        location=location,
        risk_score=result.score,
        risk_level=result.level,
    )

    if updated_roads:
        road_names = ", ".join(
            f"{road['name']} ({road['old_status']} → {road['new_status']})"
            for road in updated_roads
        )
        steps.append(f"Road connectivity updated: {road_names}")
    else:
        steps.append("Road connectivity checked - no status change")

    alert, is_new, sms = process_alert(
        db,
        location,
        result.score,
        result.level,
        result.factors,
    )

    if is_new:
        steps.append("Alert generated and SMS dispatched")
    elif alert is not None:
        steps.append("Alert already active for this risk level")
    else:
        steps.append("Risk below alert threshold - no alert needed")

    priority = compute_priority(
        db,
        location,
        result.score,
    )

    steps.append(
        f"Emergency priority computed: {priority.priority_level}"
    )

    db.commit()

    return {
        "environment": env,
        "prediction": prediction,
        "risk": result,
        "alert": alert,
        "alert_generated": is_new,
        "sms_log": sms,
        "priority": priority,
        "updated_roads": updated_roads,
        "steps": steps,
    }