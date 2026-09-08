from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SmsLog(Base):
    """Simulated SMS record.

    A real gateway (Twilio / MSG91 / Government SMS Gateway) can replace the
    simulated dispatcher in services/sms_service.py without schema changes.
    """

    __tablename__ = "sms_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    recipient_area: Mapped[str] = mapped_column(String(150))
    phone_recipients: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(String(30), default="SIMULATED_SMS")
    status: Mapped[str] = mapped_column(String(20), default="SENT")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
