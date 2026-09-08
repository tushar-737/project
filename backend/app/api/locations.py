"""Locations: monitored vulnerable points across the North Eastern Region."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Location
from ..schemas.location import LocationOut
from ..utils.queries import location_summaries

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("")
def list_locations(db: Session = Depends(get_db)):
    """All locations with their latest environment sample and risk prediction."""
    return location_summaries(db)


@router.get("/{location_id}", response_model=LocationOut)
def get_location(location_id: int, db: Session = Depends(get_db)):
    location = db.get(Location, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return LocationOut.model_validate(location)
