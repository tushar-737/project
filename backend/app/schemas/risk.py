import json
from datetime import datetime
from typing import List

from pydantic import BaseModel


class RiskPredictionOut(BaseModel):
    id: int
    location_id: int
    risk_score: float
    risk_level: str
    confidence: float
    contributing_factors: List[str]
    prediction_time: datetime

    @classmethod
    def from_row(cls, row) -> "RiskPredictionOut":
        """Build from an ORM object, parsing the JSON factors column."""
        try:
            factors = json.loads(row.contributing_factors or "[]")
        except (ValueError, TypeError):
            factors = []
        return cls(
            id=row.id,
            location_id=row.location_id,
            risk_score=row.risk_score,
            risk_level=row.risk_level,
            confidence=row.confidence,
            contributing_factors=factors if isinstance(factors, list) else [],
            prediction_time=row.prediction_time,
        )


class RiskZoneOut(BaseModel):
    """Risk overview row consumed by Risk Monitoring / Analytics / Map."""

    location_id: int
    name: str
    district: str
    state: str
    latitude: float
    longitude: float
    elevation: float
    risk_score: float
    risk_level: str
    confidence: float
    rainfall: float | None = None
    soil_moisture: float | None = None
    humidity: float | None = None
    slope_angle: float | None = None
    temperature: float | None = None
    scenario: str | None = None
    prediction_time: datetime | None = None
    last_updated: datetime | None = None
