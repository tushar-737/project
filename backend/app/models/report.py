from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Report(Base):
    """
    Citizen / field officer disaster report.

    Supports:
    - Online reports
    - Offline reports
    - Offline synchronization
    - Image/video evidence
    - Verification workflow
    """

    __tablename__ = "reports"

    # ==========================================================
    # PRIMARY IDENTIFIER
    # ==========================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # ==========================================================
    # OFFLINE SYNC IDENTIFIER
    # Generated on the client device to prevent duplicates.
    # ==========================================================

    client_report_id: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
    )

    # ==========================================================
    # REPORTER
    # ==========================================================

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    # ==========================================================
    # REPORT INFORMATION
    # ==========================================================

    report_type: Mapped[str] = mapped_column(
        String(40),
    )

    description: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    # ==========================================================
    # GEOLOCATION
    # ==========================================================

    latitude: Mapped[float] = mapped_column(
        Float,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
    )

    # ==========================================================
    # MEDIA EVIDENCE
    # ==========================================================

    image_path: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    video_path: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    # ==========================================================
    # SEVERITY
    # LOW | MODERATE | HIGH | CRITICAL
    # ==========================================================

    severity: Mapped[str] = mapped_column(
        String(20),
        default="MODERATE",
    )

    # ==========================================================
    # VERIFICATION WORKFLOW
    # PENDING | VERIFIED | REJECTED
    # ==========================================================

    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
    )

    # ==========================================================
    # LOCATION INTELLIGENCE
    # Automatically linked to nearest monitored location.
    # ==========================================================

    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id"),
        nullable=True,
    )

    # ==========================================================
    # OFFLINE SYNCHRONIZATION
    # ==========================================================

    is_offline_report: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    offline_created_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # ==========================================================
    # SERVER TIMESTAMPS
    # ==========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )