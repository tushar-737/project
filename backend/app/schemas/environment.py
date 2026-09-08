from datetime import datetime

from pydantic import BaseModel


class EnvironmentalDataOut(BaseModel):
    id: int
    location_id: int
    rainfall: float
    soil_moisture: float
    temperature: float
    humidity: float
    slope_angle: float
    scenario: str
    timestamp: datetime

    model_config = {"from_attributes": True}
