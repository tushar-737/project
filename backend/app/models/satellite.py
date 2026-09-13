from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SatelliteObservation(Base):
    """
    Stores satellite intelligence observations for
    monitored locations.
    """

    __tablename__ = "satellite_observations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    location_id: Mapped[int] = mapped_column(
        Integer,
        index=True,
    )

    vegetation_index: Mapped[float] = mapped_column(
        Float,
    )

    surface_wetness: Mapped[float] = mapped_column(
        Float,
    )

    vegetation_risk: Mapped[float] = mapped_column(
        Float,
    )

    wetness_risk: Mapped[float] = mapped_column(
        Float,
    )

    satellite_risk: Mapped[float] = mapped_column(
        Float,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
    )

    observation_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        index=True,
    )