"""Alert engine.

Rules (from the project spec):

    risk_score >= 76  ->  CRITICAL alert
    risk_score >= 51  ->  HIGH alert

A HIGH/CRITICAL alert automatically fans out to the simulated SMS service.
When a later reading drops below the alert threshold, the ACTIVE alert is
marked RESOLVED. Only one ACTIVE alert exists per location at a time (the
newest replaces the old when the level changes).
"""
from sqlalchemy.orm import Session

from ..models import Alert
from ..models.alert import utcnow


def build_alert_message(location, risk_score: float, risk_level: str,
                        factors: list[str]) -> str:
    """Human-readable warning following the mandated example format."""
    weather = ", ".join(factors) if factors else "Adverse conditions detected"
    action = (
        "Avoid all vulnerable roads, evacuate if instructed by authorities, "
        "and inspect the affected area immediately."
        if risk_level == "CRITICAL"
        else "Avoid vulnerable roads and inspect the affected area."
    )
    return (
        f"LANDSLIDE WARNING\n"
        f"Location: {location.name}\n"
        f"District: {location.district}, {location.state}\n"
        f"Risk Level: {risk_level}\n"
        f"Risk Score: {risk_score:.0f}/100\n"
        f"Reason: {weather} detected.\n"
        f"Recommended Action: {action}"
    )


def process_alert(db: Session, location, risk_score: float, risk_level: str,
                  factors: list[str]) -> tuple[Alert | None, bool, object | None]:
    """Evaluate and store alerts for one new prediction.

    Returns (active_alert, alert_generated_now, sms_log_row). Only HIGH and
    CRITICAL predictions produce alerts (plus simulated SMS broadcasts).
    """
    from .sms_service import send_alert_sms

    if risk_score < 51:
        # Conditions improved - resolve any standing warning for the site.
        for old in db.query(Alert).filter(
                Alert.location_id == location.id, Alert.status == "ACTIVE").all():
            old.status = "RESOLVED"
            old.resolved_at = utcnow()
        return None, False, None

    active = (
        db.query(Alert)
        .filter(Alert.location_id == location.id, Alert.status == "ACTIVE")
        .order_by(Alert.created_at.desc())
        .first()
    )
    # A standing alert that exactly matches the new reading is kept (no
    # duplicate); any change in level or score issues a fresh warning
    # bulletin + SMS so every escalation of the situation is visible.
    if (active is not None and active.risk_level == risk_level
            and abs(active.risk_score - risk_score) < 0.05):
        return active, False, None

    for old in db.query(Alert).filter(
            Alert.location_id == location.id, Alert.status == "ACTIVE").all():
        old.status = "RESOLVED"
        old.resolved_at = utcnow()

    message = build_alert_message(location, risk_score, risk_level, factors)
    alert = Alert(
        location_id=location.id,
        risk_level=risk_level,
        risk_score=risk_score,
        message=message,
        status="ACTIVE",
    )
    db.add(alert)
    db.flush()  # assign alert.id
    sms = send_alert_sms(db, location, risk_level, risk_score, message)
    return alert, True, sms
