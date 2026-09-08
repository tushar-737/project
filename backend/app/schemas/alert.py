from datetime import datetime

from pydantic import BaseModel


class AlertOut(BaseModel):
    id: int
    location_id: int
    location_name: str | None = None
    district: str | None = None
    state: str | None = None
    risk_level: str
    risk_score: float
    message: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
