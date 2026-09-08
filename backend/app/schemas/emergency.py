from datetime import datetime

from pydantic import BaseModel

from .location import LocationOut


class EmergencyPriorityOut(BaseModel):
    id: int
    location_id: int
    priority_level: str
    priority_score: float
    reason: str
    created_at: datetime
    location: LocationOut | None = None

    model_config = {"from_attributes": True}
