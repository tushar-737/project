from datetime import datetime
from typing import Literal

from pydantic import BaseModel

RoadStatus = Literal["OPEN", "HIGH_RISK", "PARTIALLY_BLOCKED", "BLOCKED"]
RiskLevel = Literal["LOW", "MODERATE", "HIGH", "CRITICAL"]


class RoadOut(BaseModel):
    id: int
    name: str
    district: str
    state: str
    latitude: float
    longitude: float
    end_latitude: float | None = None
    end_longitude: float | None = None
    location_id: int | None = None
    status: str
    risk_level: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoadStatusUpdate(BaseModel):
    status: RoadStatus
    # Optional: when a road changes, propagate the risk level to the linked
    # location (used by the emergency priority engine).
    risk_level: RiskLevel | None = None


class RoadStatusCounts(BaseModel):
    open: int
    high_risk: int
    partially_blocked: int
    blocked: int
