"""
NER LandslideAI - Field Intelligence Service

Converts verified citizen and field officer reports
into a risk signal for the landslide monitoring system.

Only VERIFIED reports are used as intelligence.

Examples:

SLOPE_CRACK       -> strong warning signal
SLOPE_MOVEMENT    -> very strong warning signal
LANDSLIDE         -> critical signal
ROAD_BLOCKAGE     -> connectivity/emergency signal
ROCKFALL          -> high warning signal
"""

from sqlalchemy.orm import Session

from ..models import Report


# ==========================================================
# REPORT TYPE RISK WEIGHTS
# ==========================================================

REPORT_RISK_WEIGHTS = {

    # Confirmed landslide event.
    "LANDSLIDE": 100,

    # Strong signs before landslide.
    "SLOPE_MOVEMENT": 90,

    # Structural warning signs.
    "SLOPE_CRACK": 75,

    "ROAD_CRACK": 55,

    # Rockfall may indicate slope instability.
    "ROCKFALL": 70,

    # Road blockage can be caused by slope failure.
    "ROAD_BLOCKAGE": 65,

    # Flooding contributes indirectly.
    "FLOODING": 45,

    "OTHER": 20,
}


# ==========================================================
# SEVERITY MULTIPLIERS
# ==========================================================

SEVERITY_MULTIPLIERS = {

    "LOW": 0.40,

    "MODERATE": 0.60,

    "HIGH": 0.80,

    "CRITICAL": 1.00,
}


# ==========================================================
# GET FIELD INTELLIGENCE
# ==========================================================

def get_field_intelligence(
    db: Session,
    location_id: int,
) -> dict:

    """
    Calculate field intelligence for one monitored location.

    Only VERIFIED reports are included.
    """

    reports = (

        db.query(Report)

        .filter(
            Report.location_id == location_id,
            Report.status == "VERIFIED",
        )

        .order_by(
            Report.created_at.desc()
        )

        .all()

    )

    # ------------------------------------------------------
    # NO VERIFIED REPORTS
    # ------------------------------------------------------

    if not reports:

        return {

            "field_risk": 0.0,

            "report_count": 0,

            "reports": [],

            "primary_signal": None,

        }

    # ------------------------------------------------------
    # CALCULATE REPORT SIGNALS
    # ------------------------------------------------------

    signals = []

    for report in reports:

        base_risk = REPORT_RISK_WEIGHTS.get(
            report.report_type,
            REPORT_RISK_WEIGHTS["OTHER"],
        )

        severity_multiplier = (
            SEVERITY_MULTIPLIERS.get(
                report.severity,
                0.60,
            )
        )

        signal = (
            base_risk
            *
            severity_multiplier
        )

        signals.append({

            "report_id": report.id,

            "report_type": report.report_type,

            "severity": report.severity,

            "signal": round(
                signal,
                2,
            ),

            "created_at": report.created_at,

        })

    # ------------------------------------------------------
    # COMBINE SIGNALS
    #
    # Highest report is the strongest evidence.
    #
    # Additional reports increase confidence.
    # ------------------------------------------------------

    highest_signal = max(
        signal["signal"]
        for signal in signals
    )

    report_bonus = min(

        (len(signals) - 1) * 5,

        20,

    )

    field_risk = min(

        highest_signal + report_bonus,

        100,

    )

    # ------------------------------------------------------
    # PRIMARY SIGNAL
    # ------------------------------------------------------

    primary_signal = max(

        signals,

        key=lambda item: item["signal"],

    )

    # ------------------------------------------------------
    # RETURN INTELLIGENCE
    # ------------------------------------------------------

    return {

        "field_risk": round(
            field_risk,
            2,
        ),

        "report_count": len(
            reports
        ),

        "reports": signals,

        "primary_signal": primary_signal,

    }