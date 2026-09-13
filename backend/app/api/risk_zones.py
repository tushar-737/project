from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.risk_zone_service import (
    get_all_risk_zones,
    get_high_risk_zones,
)


router = APIRouter(
    prefix="/risk-zones",
    tags=["Risk Zones"],
)


@router.get("/")
def list_risk_zones(
    minimum_score: float = Query(
        default=0,
        ge=0,
        le=100,
    ),
    db: Session = Depends(get_db),
):
    """
    Return monitored locations with their
    latest AI risk prediction.

    This endpoint is designed for:

    - GIS maps
    - Risk heatmaps
    - Dashboard monitoring
    - High-risk zone analysis
    """

    if minimum_score > 0:

        zones = get_high_risk_zones(
            db=db,
            minimum_score=minimum_score,
        )

    else:

        zones = get_all_risk_zones(
            db=db,
        )

    return {
        "total_zones": len(zones),
        "minimum_score": minimum_score,
        "zones": zones,
    }


@router.get("/high-risk")
def list_high_risk_zones(
    db: Session = Depends(get_db),
):
    """
    Return HIGH and CRITICAL risk zones.

    Default threshold: 50/100.
    """

    zones = get_high_risk_zones(
        db=db,
        minimum_score=50,
    )

    return {
        "total_high_risk_zones": len(zones),
        "zones": zones,
    }