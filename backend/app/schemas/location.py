from datetime import datetime

from pydantic import BaseModel

from .environment import EnvironmentalDataOut
from .risk import RiskPredictionOut


class LocationOut(BaseModel):
    id: int
    name: str
    district: str
    state: str
    latitude: float
    longitude: float
    elevation: float
    slope_angle: float
    historical_landslide_factor: float
    population_factor: float
    isolation_factor: float
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LocationSummary(LocationOut):
    """Location + the most recent environment sample + risk prediction.

    This is the primary payload for the dashboard and GIS map.
    """

    latest_environment: EnvironmentalDataOut | None = None
    latest_risk: RiskPredictionOut | None = None


class MapStats(BaseModel):
    location_count: int
    low: int
    moderate: int
    high: int
    critical: int
