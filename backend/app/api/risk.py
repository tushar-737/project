"""Risk endpoints: zones, detail, history and the aggregate trend.

IMPORTANT: literal routes (/zones, /zones/summary, /trend/overview) are
declared BEFORE the parameterised /{location_id} routes so FastAPI never
tries to parse a word like "trend" as an integer.
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
from ..utils.queries import latest_environment_by_location, latest_risk_by_location

router = APIRouter(prefix="/risk", tags=["risk"])


def _build_zones(db: Session, state: str | None, level: str | None) -> list[dict]:
    query = db.query(Location).filter(Location.is_active.is_(True))
    if state:
        query = query.filter(Location.state == state)
    locations = query.order_by(Location.state, Location.name).all()

    env_map = latest_environment_by_location(db)
    risk_map = latest_risk_by_location(db)

    zones = []
    for loc in locations:
        pred = risk_map.get(loc.id)
        if level and (not pred or pred.risk_level != level):
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
            "risk_score": pred.risk_score if pred else 0.0,
            "risk_level": pred.risk_level if pred else "LOW",
            "confidence": pred.confidence if pred else 0.0,
            "rainfall": env.rainfall if env else None,
            "soil_moisture": env.soil_moisture if env else None,
            "humidity": env.humidity if env else None,
            "slope_angle": env.slope_angle if env else loc.slope_angle,
            "temperature": env.temperature if env else None,
            "scenario": env.scenario if env else None,
            "prediction_time": pred.prediction_time if pred else None,
            "last_updated": env.timestamp if env else None,
        })
    zones.sort(key=lambda z: z["risk_score"], reverse=True)
    return zones


@router.get("/zones")
def risk_zones(
    state: str | None = Query(default=None),
    level: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Current risk overview for every active location (filterable)."""
    return _build_zones(db, state, level)


@router.get("/zones/summary")
def risk_zone_summary(db: Session = Depends(get_db)):
    """Counts per risk level - powers dashboard cards and charts."""
    zones = _build_zones(db, None, None)
    summary = {"low": 0, "moderate": 0, "high": 0, "critical": 0, "total": len(zones)}
    for z in zones:
        key = z["risk_level"].lower()
        if key in summary:
            summary[key] += 1
    return summary


@router.get("/trend/overview")
def risk_trend(db: Session = Depends(get_db)):
    """Aggregated recent risk across all locations (hourly buckets, 72h)."""
    latest = (
        db.query(RiskPrediction)
        .order_by(RiskPrediction.prediction_time.desc())
        .first()
    )
    cutoff = latest.prediction_time - timedelta(hours=72) if latest else None
    rows = db.query(RiskPrediction).order_by(RiskPrediction.prediction_time.asc()).all()
    if cutoff:
        rows = [r for r in rows if r.prediction_time >= cutoff]

    buckets: dict[str, list[float]] = {}
    for r in rows:
        key = r.prediction_time.strftime("%Y-%m-%dT%H:00:00")
        buckets.setdefault(key, []).append(r.risk_score)
    return [
        {"time": key, "avg_score": round(sum(v) / len(v), 1),
         "samples": len(v), "max_score": round(max(v), 1)}
        for key, v in sorted(buckets.items())
    ]
@router.post("/{location_id}/predict")
def predict_location_risk(
    location_id: int,
    db: Session = Depends(get_db),
):
    """
    Run the ML risk engine using the latest environmental
    data available for this location.
    """

    location = db.get(Location, location_id)

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    # Get latest environmental data
    env_map = latest_environment_by_location(db)
    env = env_map.get(location_id)

    if not env:
        raise HTTPException(
            status_code=404,
            detail="No environmental data available for this location",
        )

    # Run ML prediction
    result = predict_landslide_risk(
        rainfall=env.rainfall or 0,
        soil_moisture=env.soil_moisture or 0,
        slope_angle=env.slope_angle or location.slope_angle or 0,
    )

    # Save prediction in database
    prediction = RiskPrediction(
        location_id=location_id,
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        confidence=result["confidence"],
        contributing_factors=str(result["contributing_factors"]),
    )

    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return {
        "location": location.name,
        "location_id": location.id,
        "prediction": RiskPredictionOut.from_row(prediction),
    }
@router.post("/predict-all")
def predict_all_locations(
    db: Session = Depends(get_db),
):
    """
    Run the ML risk prediction for all active locations
    using their latest environmental data.
    """

    locations = (
        db.query(Location)
        .filter(Location.is_active.is_(True))
        .all()
    )

    env_map = latest_environment_by_location(db)

    results = []
    skipped = []

    for location in locations:

        env = env_map.get(location.id)

        # Skip locations with no environmental data
        if not env:
            skipped.append({
                "location_id": location.id,
                "name": location.name,
                "reason": "No environmental data",
            })
            continue

        # Run ML model
        result = predict_landslide_risk(
            rainfall=env.rainfall or 0,
            soil_moisture=env.soil_moisture or 0,
            slope_angle=env.slope_angle or location.slope_angle or 0,
        )

        # Create database prediction
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

        results.append({
            "location_id": location.id,
            "location": location.name,
            "risk_score": result["risk_score"],
            "risk_level": result["risk_level"],
        })

    # Save all predictions together
    db.commit()

    return {
        "message": "ML prediction completed",
        "locations_processed": len(results),
        "locations_skipped": len(skipped),
        "predictions": results,
        "skipped": skipped,
    }
@router.get("/{location_id}/history")
def risk_history(
    location_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Time series of past predictions for one location (oldest first)."""
    if not db.get(Location, location_id):
        raise HTTPException(status_code=404, detail="Location not found")
    rows = (
        db.query(RiskPrediction)
        .filter(RiskPrediction.location_id == location_id)
        .order_by(RiskPrediction.prediction_time.desc())
        .limit(limit)
        .all()
    )
    rows.reverse()
    return [RiskPredictionOut.from_row(r) for r in rows]


@router.get("/{location_id}")
def risk_detail(location_id: int, db: Session = Depends(get_db)):
    """Location + latest environment + latest prediction for one site."""
    location = db.get(Location, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    env = latest_environment_by_location(db).get(location_id)
    pred = latest_risk_by_location(db).get(location_id)
    return {
        "location": LocationOut.model_validate(location),
        "environment": EnvironmentalDataOut.model_validate(env) if env else None,
        "risk": RiskPredictionOut.from_row(pred) if pred else None,
    }
