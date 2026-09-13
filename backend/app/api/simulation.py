from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Location, RiskPrediction
from ..schemas.environment import EnvironmentalDataOut
from ..schemas.simulation import Scenario, SimulationRequest, SimulationOut
from ..services.pipeline import run_risk_pipeline
from ..services.sensor_service import SimulatedSensorService


router = APIRouter(prefix="/simulation", tags=["simulation"])

_sensor = SimulatedSensorService()


def _simulation_out(
    location: Location,
    scenario: str,
    result: dict,
    steps: list[str],
) -> SimulationOut:
    env = result["environment"]
    risk = result["risk"]
    alert = result["alert"]
    priority = result["priority"]
    sms = result.get("sms_log")

    return SimulationOut(
        location_id=location.id,
        location_name=location.name,
        district=location.district,
        state=location.state,
        scenario=scenario,
        environment_id=env.id,
        rainfall=env.rainfall,
        soil_moisture=env.soil_moisture,
        temperature=env.temperature,
        humidity=env.humidity,
        slope_angle=env.slope_angle,
        risk_score=risk.score,
        risk_level=risk.level,
        confidence=risk.confidence,
        contributing_factors=risk.factors,
        alert_id=alert.id if alert else None,
        alert_message=alert.message if alert else None,
        sms_log_id=sms.id if sms else None,
        priority_level=priority.priority_level if priority else None,
        priority_score=priority.priority_score if priority else None,
        timestamp=env.timestamp,
        pipeline_steps=steps,
    )


def _alert_pipeline_step(result: dict) -> str:
    alert = result.get("alert")
    alert_generated = result.get("alert_generated", False)
    sms = result.get("sms_log")

    if alert_generated and alert:
        if sms:
            return (
                f"New alert #{alert.id} generated "
                f"({alert.risk_level}) + SMS broadcast logged"
            )

        return (
            f"New alert #{alert.id} generated "
            f"({alert.risk_level})"
        )

    if alert:
        return (
            f"Alert #{alert.id} is already active "
            f"({alert.risk_level}) - no duplicate SMS sent"
        )

    return "No alert required (risk below threshold)"


def _road_pipeline_step(result: dict) -> str:
    updated_roads = result.get("updated_roads", [])

    if not updated_roads:
        return "Road connectivity checked - no status change"

    road_updates = []

    for road in updated_roads:
        road_updates.append(
            f"{road['name']} "
            f"({road['old_status']} -> {road['new_status']})"
        )

    return (
        "Road connectivity updated: "
        + ", ".join(road_updates)
    )


@router.post("/environment")
def generate_environment(
    payload: SimulationRequest,
    db: Session = Depends(get_db),
):
    location = db.get(
        Location,
        payload.location_id,
    )

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    sample = _sensor.read(
        location,
        scenario=payload.scenario,
    )

    from ..models import EnvironmentalData

    env = EnvironmentalData(
        location_id=location.id,
        rainfall=sample.rainfall,
        soil_moisture=sample.soil_moisture,
        temperature=sample.temperature,
        humidity=sample.humidity,
        slope_angle=sample.slope_angle,
        scenario=sample.scenario,
    )

    db.add(env)
    db.commit()
    db.refresh(env)

    return EnvironmentalDataOut.model_validate(env)


@router.post("/run", response_model=SimulationOut)
def run_simulation(
    payload: SimulationRequest,
    db: Session = Depends(get_db),
):
    location = db.get(
        Location,
        payload.location_id,
    )

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    if payload.scenario not in Scenario.__args__:
        raise HTTPException(
            status_code=422,
            detail="Unknown scenario",
        )

    sample = _sensor.read(
        location,
        scenario=payload.scenario,
    )

    result = run_risk_pipeline(
        db,
        location,
        sample,
    )

    steps = [
        (
            f"Generated {payload.scenario} environmental sample "
            f"({sample.rainfall:.0f} mm rainfall, "
            f"{sample.soil_moisture:.0f}% soil moisture)"
        ),
        "Sent sample to backend and stored it",
        "AI risk engine executed",
        (
            f"Risk score {result['risk'].score:.1f}/100 - "
            f"{result['risk'].level}"
        ),
        "Risk prediction saved",
        _road_pipeline_step(result),
        _alert_pipeline_step(result),
        (
            f"Emergency priority updated to "
            f"{result['priority'].priority_level}"
        ),
    ]

    return _simulation_out(
        location,
        payload.scenario,
        result,
        steps,
    )


@router.post("/run-demo", response_model=SimulationOut)
def run_demo(
    db: Session = Depends(get_db),
):
    latest_preds = (
        db.query(RiskPrediction)
        .order_by(
            RiskPrediction.prediction_time.desc()
        )
        .all()
    )

    order: dict[int, float] = {}

    for prediction in latest_preds:
        order.setdefault(
            prediction.location_id,
            prediction.risk_score,
        )

    location = None

    for loc in (
        db.query(Location)
        .filter(Location.is_active.is_(True))
        .all()
    ):
        if location is None:
            location = loc

        elif (
            order.get(loc.id, 0)
            > order.get(location.id, 0)
        ):
            location = loc

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="No active monitored locations found",
        )

    scenario: Scenario = "EXTREME_RAIN"

    sample = _sensor.read(
        location,
        scenario=scenario,
    )

    result = run_risk_pipeline(
        db,
        location,
        sample,
    )

    steps = [
        (
            f"Auto-selected highest-risk location: "
            f"{location.name} "
            f"({location.district}, {location.state})"
        ),
        (
            f"Generated {scenario} environmental sample "
            f"({sample.rainfall:.0f} mm rainfall, "
            f"{sample.soil_moisture:.0f}% soil moisture)"
        ),
        "Sent sample to backend and stored it",
        "AI risk engine executed",
        (
            f"Risk score {result['risk'].score:.1f}/100 - "
            f"{result['risk'].level}"
        ),
        "Risk prediction saved",
        _road_pipeline_step(result),
        _alert_pipeline_step(result),
        (
            f"Emergency priority updated to "
            f"{result['priority'].priority_level}"
        ),
    ]

    return _simulation_out(
        location,
        scenario,
        result,
        steps,
    )