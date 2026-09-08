from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Location(Base):
    """A monitored vulnerable location in the North Eastern Region."""

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    district: Mapped[str] = mapped_column(String(120))
    state: Mapped[str] = mapped_column(String(60), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    elevation: Mapped[float] = mapped_column(Float, default=0)          # metres
    slope_angle: Mapped[float] = mapped_column(Float, default=0)        # degrees (baseline terrain slope)
    # Static susceptibility factor (0-1) derived from the landslide history
    # of the area. Used as an input to the risk engine.
    historical_landslide_factor: Mapped[float] = mapped_column(Float, default=0.2)
    # 0-1 factors consumed by the emergency priority engine.
    population_factor: Mapped[float] = mapped_column(Float, default=0.5)
    isolation_factor: Mapped[float] = mapped_column(Float, default=0.5)  # 1 = remote / hard to reach
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
