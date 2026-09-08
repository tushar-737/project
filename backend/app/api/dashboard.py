"""Dashboard summary endpoint (single payload for the landing page)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Alert, Location, Report, Road
from ..utils.queries import location_summaries

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _alert_out(a, loc):
    return {
        "id": a.id, "location_id": a.location_id,
        "location_name": loc.name if loc else None,
        "district": loc.district if loc else None,
        "state": loc.state if loc else None,
        "risk_level": a.risk_level, "risk_score": a.risk_score,
        "message": a.message, "status": a.status, "created_at": a.created_at,
    }


def _report_out(r, user=None):
    return {
        "id": r.id, "user_id": r.user_id,
        "reporter_name": user.name if user else None,
        "report_type": r.report_type, "description": r.description,
        "latitude": r.latitude, "longitude": r.longitude,
        "image_url": f"/uploads/{r.image_path.split('/')[-1]}" if r.image_path else None,
        "status": r.status, "created_at": r.created_at,
    }


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    """Everything the main dashboard renders in one request.

    No hardcoded values - every number is computed from live database rows.
    """
    from ..models import User

    zones = location_summaries(db)

    def risk_level_of(z: dict) -> str:
        r = z["latest_risk"]
        return r.risk_level if r else "LOW"

    distribution = {"low": 0, "moderate": 0, "high": 0, "critical": 0}
    for z in zones:
        key = risk_level_of(z).lower()
        if key in distribution:
            distribution[key] += 1

    roads = db.query(Road).all()
    road_counts = {"open": 0, "high_risk": 0, "partially_blocked": 0, "blocked": 0}
    for r in roads:
        key = r.status.lower()
        if key in road_counts:
            road_counts[key] += 1

    alerts = (db.query(Alert).order_by(Alert.created_at.desc()).limit(50).all())
    alert_counts = {"high": 0, "critical": 0, "total_active": 0}
    for a in alerts:
        if a.status == "ACTIVE":
            alert_counts["total_active"] += 1
            if a.risk_level in ("HIGH", "CRITICAL"):
                alert_counts[a.risk_level.lower()] += 1

    reports = db.query(Report).order_by(Report.created_at.desc()).limit(200).all()
    pending = sum(1 for r in reports if r.status == "PENDING")

    # Per-state weather outlook: mean rainfall/humidity of latest samples and
    # the dominant current risk level of locations in that state.
    states = {}
    for z in zones:
        env = z["latest_environment"]
        states.setdefault(z["state"], {"rainfall": [], "humidity": [], "levels": []})
        if env:
            states[z["state"]]["rainfall"].append(env.rainfall)
            states[z["state"]]["humidity"].append(env.humidity)
        states[z["state"]]["levels"].append(risk_level_of(z))
    outlook = []
    for state, agg in states.items():
        from collections import Counter
        dominant = Counter(agg["levels"]).most_common(1)[0][0] if agg["levels"] else "LOW"
        outlook.append({
            "state": state,
            "avg_rainfall": round(sum(agg["rainfall"]) / len(agg["rainfall"]), 1) if agg["rainfall"] else 0,
            "avg_humidity": round(sum(agg["humidity"]) / len(agg["humidity"]), 1) if agg["humidity"] else 0,
            "outlook": dominant,
            "locations": len(agg["levels"]),
        })
    outlook.sort(key=lambda o: {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "LOW": 3}[o["outlook"]])

    users = {u.id: u for u in db.query(User).all()}
    return {
        "counts": {
            "high_risk_zones": distribution["high"] + distribution["critical"],
            "critical_zones": distribution["critical"],
            "critical_alerts": alert_counts["critical"],
            "active_alerts": alert_counts["total_active"],
            "blocked_roads": road_counts["blocked"],
            "partially_blocked_roads": road_counts["partially_blocked"],
            "active_reports": pending,
            "locations": len(zones),
            "states": len(states),
        },
        "distribution": distribution,
        "recent_alerts": [_alert_out(a, db.get(Location, a.location_id)) for a in alerts[:6]],
        "recent_reports": [
            _report_out(r, users.get(r.user_id)) for r in reports[:6]
        ],
        "weather_outlook": outlook,
        "road_counts": road_counts,
        "report_counts": {"pending": pending,
                          "verified": sum(1 for r in reports if r.status == "VERIFIED"),
                          "rejected": sum(1 for r in reports if r.status == "REJECTED")},
        "top_risk": sorted(
            [{
                "location_id": z["id"], "name": z["name"], "state": z["state"],
                "risk_score": z["latest_risk"].risk_score if z["latest_risk"] else 0,
                "risk_level": risk_level_of(z),
            } for z in zones],
            key=lambda x: x["risk_score"], reverse=True,
        )[:5],
    }
