"""Simulation Center endpoints.

POST /api/simulation/environment  - generate & store one environmental sample
POST /api/simulation/run          - full pipeline for chosen location/scenario
POST /api/simulation/run-demo     - one-click extreme-rain demo on the
                                    currently highest-risk location

Every "run" executes the same automatic workflow used by real sensor
ingestion: sample -> risk engine -> prediction -> alert -> SMS -> priority.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Location, RiskPrediction
from ..schemas.environment import EnvironmentalDataOut
from ..schemas.simulation import Scenario, SimulationRequest, SimulationOut
from ..services.pipeline import run_risk_pipeline
from ..services.sensor_service import SCENARIO_LABELS, SimulatedSensorService

router = APIRouter(prefix="/simulation", tags=["simulation"])

_sensor = SimulatedSensorService()


def _simulation_out(location: Location, scenario: str, result: dict,
                    steps: list[str]) -> SimulationOut:
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


@router.post("/environment")
def generate_environment(payload: SimulationRequest, db: Session = Depends(get_db)):
    """STEP 1-3 of the workflow: generate and persist one sample.

    The sample is stored but does NOT trigger the risk engine; use
    /simulation/run for the complete workflow in one call.
    """
    location = db.get(Location, payload.location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    sample = _sensor.read(location, scenario=payload.scenario)
    from ..models import EnvironmentalData
    env = EnvironmentalData(
        location_id=location.id,
        rainfall=sample.rainfall, soil_moisture=sample.soil_moisture,
        temperature=sample.temperature, humidity=sample.humidity,
        slope_angle=sample.slope_angle, scenario=sample.scenario,
    )
    db.add(env)
    db.commit()
    db.refresh(env)
    return EnvironmentalDataOut.model_validate(env)


@router.post("/run", response_model=SimulationOut)
def run_simulation(payload: SimulationRequest, db: Session = Depends(get_db)):
    """Run the complete 8-step automatic pipeline for one scenario."""
    location = db.get(Location, payload.location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    if payload.scenario not in Scenario.__args__:
        raise HTTPException(status_code=422, detail="Unknown scenario")

    sample = _sensor.read(location, scenario=payload.scenario)
    result = run_risk_pipeline(db, location, sample)

    steps = [
        f"Generated {payload.scenario} environmental sample "
        f"({sample.rainfall:.0f} mm rainfall, {sample.soil_moisture:.0f}% soil moisture)",
        "Sent sample to backend and stored it",
        "AI risk engine executed",
        f"Risk score {result['risk'].score:.1f}/100 - {result['risk'].level}",
        "Risk prediction saved",
        "GIS/location record updated",
    ]
    if result["alert"]:
        steps.append(f"Alert #{result['alert'].id} generated ({result['alert'].risk_level}) + SMS broadcast logged")
    else:
        steps.append("No new alert required (risk below threshold or unchanged)")
    steps.append(f"Emergency priority updated to {result['priority'].priority_level}")

    return _simulation_out(location, payload.scenario, result, steps)


@router.post("/run-demo", response_model=SimulationOut)
def run_demo(db: Session = Depends(get_db)):
    """🚨 One-click demo: EXTREME RAIN on the currently highest-risk site."""
    latest_preds = (
        db.query(RiskPrediction)
        .order_by(RiskPrediction.prediction_time.desc())
        .all()
    )
    order: dict[int, float] = {}
    for p in latest_preds:
        order.setdefault(p.location_id, p.risk_score)

    location = None
    for loc in db.query(Location).filter(Location.is_active.is_(True)).all():
        if location is None or order.get(loc.id, 0) > order.get(location.id, 0):
            location = loc

    scenario: Scenario = "EXTREME_RAIN"
    sample = _sensor.read(location, scenario=scenario)
    result = run_risk_pipeline(db, location, sample)

    steps = [
        f"Auto-selected highest-risk location: {location.name} "
        f"({location.district}, {location.state})",
        f"Generated {scenario} environmental sample "
        f"({sample.rainfall:.0f} mm rainfall, {sample.soil_moisture:.0f}% soil moisture)",
        "Sent sample to backend and stored it",
        "AI risk engine executed",
        f"Risk score {result['risk'].score:.1f}/100 - {result['risk'].level}",
        "Risk prediction saved",
        "GIS/location record updated",
    ]
    if result["alert"]:
        steps.append(f"Alert #{result['alert'].id} generated ({result['alert'].risk_level}) + SMS broadcast logged")
    else:
        steps.append("No new alert required (risk below threshold or unchanged)")
    steps.append(f"Emergency priority updated to {result['priority'].priority_level}")

    return _simulation_out(location, scenario, result, steps)
