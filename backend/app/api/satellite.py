from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Location
from ..services.satellite_service import get_satellite_intelligence
from ..services.weather_service import get_weather_sample

from .deps import get_current_user


router = APIRouter(
    prefix="/satellite",
    tags=["Satellite Intelligence"],
)


@router.get("/{location_id}")
def get_location_satellite_intelligence(
    location_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    Return satellite intelligence indicators
    for a monitored location.
    """

    location = (
        db.query(Location)
        .filter(
            Location.id == location_id,
            Location.is_active == True,
        )
        .first()
    )

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    # Get current environmental data.
    sample = get_weather_sample(location)

    # Generate satellite intelligence.
    satellite = get_satellite_intelligence(
        location=location,
        rainfall_24h=sample.rainfall,
        rainfall_72h=sample.rainfall_72h,
        soil_moisture=sample.soil_moisture,
    )

    return {
        "location": {
            "id": location.id,
            "name": location.name,
            "district": location.district,
            "state": location.state,
            "latitude": location.latitude,
            "longitude": location.longitude,
        },
        "satellite": satellite.as_dict(),
    }