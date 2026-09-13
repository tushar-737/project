"""Alert engine.

Landslide alert rules:

    LOW / MODERATE
        No alert

    HIGH
        Generate HIGH alert

    CRITICAL
        Generate CRITICAL alert

Only one ACTIVE alert exists per location.
"""

from sqlalchemy.orm import Session

from ..models import Alert
from ..models.alert import utcnow


ALERT_LEVELS = {"HIGH", "CRITICAL"}


def build_alert_message(
    location,
    risk_score: float,
    risk_level: str,
    factors: list[str],
) -> str:
    """Create a human-readable landslide warning."""

    weather = (
        ", ".join(factors)
        if factors
        else "Adverse environmental conditions"
    )

    if risk_level == "CRITICAL":

        action = (
            "Avoid vulnerable roads. "
            "Evacuate if instructed by authorities. "
            "Emergency inspection is recommended immediately."
        )

    else:

        action = (
            "Avoid vulnerable roads and remain alert. "
            "Authorities should inspect the affected area."
        )

    return (
        "LANDSLIDE WARNING\n\n"
        f"Location: {location.name}\n"
        f"District: {location.district}, {location.state}\n"
        f"Risk Level: {risk_level}\n"
        f"Risk Score: {risk_score:.2f}/100\n\n"
        f"Contributing Factors:\n"
        f"{weather}\n\n"
        f"Recommended Action:\n"
        f"{action}"
    )


def resolve_active_alerts(
    db: Session,
    location_id: int,
):
    """Resolve all active alerts for a location."""

    active_alerts = (
        db.query(Alert)
        .filter(
            Alert.location_id == location_id,
            Alert.status == "ACTIVE",
        )
        .all()
    )

    for alert in active_alerts:

        alert.status = "RESOLVED"

        alert.resolved_at = utcnow()


def process_alert(
    db: Session,
    location,
    risk_score: float,
    risk_level: str,
    factors: list[str],
) -> tuple[Alert | None, bool, object | None]:

    """
    Process alert state.

    Returns:

        (
            active_alert,
            alert_generated,
            sms_log
        )
    """

    from .sms_service import send_alert_sms


    # ==========================================
    # LOW / MODERATE
    # ==========================================

    if risk_level not in ALERT_LEVELS:

        resolve_active_alerts(
            db,
            location.id,
        )

        return None, False, None


    # ==========================================
    # FIND ACTIVE ALERT
    # ==========================================

    active = (
        db.query(Alert)
        .filter(
            Alert.location_id == location.id,
            Alert.status == "ACTIVE",
        )
        .order_by(
            Alert.created_at.desc()
        )
        .first()
    )


    # ==========================================
    # SAME ALERT LEVEL
    #
    # Do not repeatedly send SMS alerts.
    # ==========================================

    if active is not None:

        if active.risk_level == risk_level:

            return active, False, None


        # Risk level changed.
        # Resolve previous alert.

        active.status = "RESOLVED"

        active.resolved_at = utcnow()


    # ==========================================
    # CREATE NEW ALERT
    # ==========================================

    message = build_alert_message(

        location,
        risk_score,
        risk_level,
        factors,

    )


    alert = Alert(

        location_id=location.id,

        risk_level=risk_level,

        risk_score=risk_score,

        message=message,

        status="ACTIVE",

    )


    db.add(alert)

    db.flush()


    # ==========================================
    # SEND SMS
    # ==========================================

    sms = send_alert_sms(

        db,
        location,
        risk_level,
        risk_score,
        message,

    )


    return (

        alert,

        True,

        sms,

    )