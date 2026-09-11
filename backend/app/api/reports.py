"""Citizen & field reporting endpoints with image upload and verification."""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ..config import (
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_IMAGE_SIZE_BYTES,
    ALLOWED_VIDEO_EXTENSIONS,
    MAX_VIDEO_SIZE_BYTES,
    UPLOAD_DIR,
)
from ..database import get_db
from ..models import Report, User
from ..schemas.report import ReportVerify
from .deps import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])

REPORT_TYPES = ["LANDSLIDE", "ROAD_BLOCKAGE", "ROAD_CRACK", "SLOPE_CRACK",
                "SLOPE_MOVEMENT", "ROCKFALL", "FLOODING", "OTHER"]


def _out(report: Report, reporter: User | None = None) -> dict:
    return {
        "id": report.id,
        "user_id": report.user_id,
        "reporter_name": reporter.name if reporter else None,
        "report_type": report.report_type,
        "description": report.description,
        "latitude": report.latitude,
        "longitude": report.longitude,
        "image_url": f"/uploads/{Path(report.image_path).name}" if report.image_path else None,
        "video_url": f"/uploads/{Path(report.video_path).name}" if report.video_path else None,
        "status": report.status,
        "created_at": report.created_at,
    }


@router.post("")
def create_report(
    report_type: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    description: str = Form(default=""),
    image: UploadFile | None = File(default=None),
    video: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a field/citizen report. Supports one photo upload."""
    report_type = report_type.strip().upper()
    if report_type not in REPORT_TYPES:
        raise HTTPException(status_code=422, detail=f"report_type must be one of {REPORT_TYPES}")
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise HTTPException(status_code=422, detail="Invalid coordinates")

    image_path = None
    if image is not None and image.filename:
        suffix = Path(image.filename).suffix.lower()
        if suffix not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(status_code=422, detail="Only JPG, JPEG or PNG images are accepted")
        content = image.file.read()
        if len(content) > MAX_IMAGE_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="Image exceeds the 5 MB size limit")
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}{suffix}"
        (UPLOAD_DIR / filename).write_bytes(content)
        image_path = filename
        

    video_path = None
    if video is not None and video.filename:
        suffix = Path(video.filename).suffix.lower()
        if suffix not in ALLOWED_VIDEO_EXTENSIONS:
            raise HTTPException(status_code=422, detail="Only MP4 or WebM videos are accepted")
        content = video.file.read()
        if len(content) > MAX_VIDEO_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="Video exceeds the 20 MB size limit")
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}{suffix}"
        (UPLOAD_DIR / filename).write_bytes(content)
        video_path = filename

    report = Report(
        user_id=user.id,
        report_type=report_type,
        description=(description or "").strip(),
        latitude=latitude,
        longitude=longitude,
        image_path=image_path,
           video_path=video_path,
        status="PENDING",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return _out(report, user)


@router.get("")
def list_reports(
    status: str | None = Query(default=None),
    report_type: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """All reports, newest first. Optional filters: status, report_type."""
    query = db.query(Report)
    if status:
        query = query.filter(Report.status == status.upper())
    if report_type:
        query = query.filter(Report.report_type == report_type.upper())
    rows = query.order_by(Report.created_at.desc()).limit(limit).all()
    users = {u.id: u for u in db.query(User).all()}
    return [_out(r, users.get(r.user_id)) for r in rows]


@router.put("/{report_id}/verify")
def verify_report(
    report_id: int,
    payload: ReportVerify,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mark a report VERIFIED or REJECTED (ADMIN / FIELD_OFFICER only)."""
    if user.role not in ("ADMIN", "FIELD_OFFICER"):
        raise HTTPException(status_code=403, detail="Only officers can verify reports")
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = payload.status
    db.commit()
    db.refresh(report)
    return _out(report, user)


@router.get("/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _out(report)
