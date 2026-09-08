from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class EmergencyPriority(Base):
    """Latest computed emergency response priority for a location."""

    __tablename__ = "emergency_priorities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), unique=True, index=True)
    # PRIORITY 1 | PRIORITY 2 | PRIORITY 3
    priority_level: Mapped[str] = mapped_column(String(20))
    priority_score: Mapped[float] = mapped_column(Float)  # 0-100
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
