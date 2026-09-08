from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ReportType = Literal[
    "LANDSLIDE",
    "ROAD_BLOCKAGE",
    "ROAD_CRACK",
    "SLOPE_CRACK",
    "SLOPE_MOVEMENT",
    "ROCKFALL",
    "FLOODING",
    "OTHER",
]


class ReportCreate(BaseModel):
    report_type: ReportType = "OTHER"
    description: str = Field(default="", max_length=2000)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    reported_at: datetime | None = None  # client-side timestamp (offline sync)


class ReportVerify(BaseModel):
    status: Literal["VERIFIED", "REJECTED"]
    note: str = Field(default="", max_length=500)


class ReportOut(BaseModel):
    id: int
    user_id: int | None = None
    reporter_name: str | None = None
    report_type: str
    description: str
    latitude: float
    longitude: float
    image_url: str | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
