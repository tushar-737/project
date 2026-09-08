from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Scenario = Literal["NORMAL", "MODERATE_RAIN", "HEAVY_RAIN", "EXTREME_RAIN"]


class SimulationRequest(BaseModel):
    location_id: int
    scenario: Scenario = "HEAVY_RAIN"


class SimulationOut(BaseModel):
    location_id: int
    location_name: str
    district: str
    state: str
    scenario: str
    environment_id: int | None = None
    rainfall: float
    soil_moisture: float
    temperature: float
    humidity: float
    slope_angle: float
    risk_score: float
    risk_level: str
    confidence: float
    contributing_factors: list[str]
    alert_id: int | None = None
    alert_message: str | None = None
    sms_log_id: int | None = None
    priority_level: str | None = None
    priority_score: float | None = None
    timestamp: datetime
    pipeline_steps: list[str]


class SmsLogOut(BaseModel):
    id: int
    location_id: int
    recipient_area: str
    phone_recipients: int
    message: str
    channel: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
