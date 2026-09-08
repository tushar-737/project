from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Road(Base):
    """A road / highway corridor monitored for connectivity.

    (latitude, longitude) is the start point; (end_latitude, end_longitude)
    is the far end so the GIS map can render the road as a polyline.
    """

    __tablename__ = "roads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    district: Mapped[str] = mapped_column(String(120))
    state: Mapped[str] = mapped_column(String(60))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    end_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    end_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    # OPEN | HIGH_RISK | PARTIALLY_BLOCKED | BLOCKED
    status: Mapped[str] = mapped_column(String(30), default="OPEN")
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW")
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
