from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RiskPrediction(Base):
    """Output of the AI risk engine for one location at one point in time."""

    __tablename__ = "risk_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    risk_score: Mapped[float] = mapped_column(Float)            # 0-100
    risk_level: Mapped[str] = mapped_column(String(20))         # LOW/MODERATE/HIGH/CRITICAL
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    contributing_factors: Mapped[str] = mapped_column(Text, default="[]")  # JSON list of strings
    prediction_time: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
