from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class EnvironmentalData(Base):
    """One environmental sample (real sensor or simulation) per location."""

    __tablename__ = "environmental_data"
    __table_args__ = (Index("ix_env_loc_time", "location_id", "timestamp"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    rainfall: Mapped[float] = mapped_column(Float)          # mm / 24h
    soil_moisture: Mapped[float] = mapped_column(Float)     # %
    temperature: Mapped[float] = mapped_column(Float)       # deg C
    humidity: Mapped[float] = mapped_column(Float)          # %
    slope_angle: Mapped[float] = mapped_column(Float)       # degrees
    # scenario that produced this sample: NORMAL/MODERATE_RAIN/HEAVY_RAIN/EXTREME_RAIN
    scenario: Mapped[str] = mapped_column(String(30), default="NORMAL")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
