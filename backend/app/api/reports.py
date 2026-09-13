"""Citizen & field reporting endpoints.

Supports:

- Geo-tagged citizen reports
- Image and video evidence
- Severity classification
- Automatic nearest-location linking
- Offline report synchronization
- Officer verification workflow
"""

import uuid

from datetime import datetime, timezone

from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)

from sqlalchemy.orm import Session

from ..config import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    MAX_IMAGE_SIZE_BYTES,
    MAX_VIDEO_SIZE_BYTES,
    UPLOAD_DIR,
)

from ..database import get_db

from ..models import Location, Report, User

from ..schemas.report import (
    OfflineReportSync,
    ReportVerify,
)

from .deps import get_current_user


# ==========================================================
# ROUTER
# ==========================================================

router = APIRouter(
    prefix="/reports",
    tags=["reports"],
)


# ==========================================================
# REPORT TYPES
# ==========================================================

REPORT_TYPES = [

    "LANDSLIDE",

    "ROAD_BLOCKAGE",

    "ROAD_CRACK",

    "SLOPE_CRACK",

    "SLOPE_MOVEMENT",

    "ROCKFALL",

    "FLOODING",

    "OTHER",

]


# ==========================================================
# SEVERITY LEVELS
# ==========================================================

SEVERITY_LEVELS = [

    "LOW",

    "MODERATE",

    "HIGH",

    "CRITICAL",

]


# ==========================================================
# UTC TIME
# ==========================================================

def utcnow() -> datetime:

    return datetime.now(
        timezone.utc
    ).replace(
        tzinfo=None
    )


# ==========================================================
# FIND NEAREST MONITORED LOCATION
#
# Simple geographic distance calculation.
#
# Suitable for the SIH prototype.
# ==========================================================

def find_nearest_location(

    db: Session,

    latitude: float,

    longitude: float,

) -> Location | None:

    locations = (

        db.query(Location)

        .filter(
            Location.is_active == True
        )

        .all()

    )

    if not locations:

        return None

    nearest_location = None

    nearest_distance = float("inf")

    for location in locations:

        # Simple squared geographic distance.
        #
        # Good enough for nearest-location matching
        # in the SIH prototype.

        distance = (

            (location.latitude - latitude) ** 2

            +

            (location.longitude - longitude) ** 2

        )

        if distance < nearest_distance:

            nearest_distance = distance

            nearest_location = location

    return nearest_location


# ==========================================================
# OUTPUT FORMAT
# ==========================================================

def _out(

    report: Report,

    reporter: User | None = None,

    location: Location | None = None,

) -> dict:

    return {

        "id": report.id,

        # --------------------------------------------------
        # REPORTER
        # --------------------------------------------------

        "user_id": report.user_id,

        "reporter_name": (

            reporter.name

            if reporter

            else None

        ),

        # --------------------------------------------------
        # REPORT INFORMATION
        # --------------------------------------------------

        "report_type": report.report_type,

        "description": report.description,

        # --------------------------------------------------
        # GEOLOCATION
        # --------------------------------------------------

        "latitude": report.latitude,

        "longitude": report.longitude,

        # --------------------------------------------------
        # LINKED MONITORED LOCATION
        # --------------------------------------------------

        "location_id": report.location_id,

        "location_name": (

            location.name

            if location

            else None

        ),

        "district": (

            location.district

            if location

            else None

        ),

        "state": (

            location.state

            if location

            else None

        ),

        # --------------------------------------------------
        # SEVERITY
        # --------------------------------------------------

        "severity": report.severity,

        # --------------------------------------------------
        # MEDIA
        # --------------------------------------------------

        "image_url": (

            f"/uploads/{Path(report.image_path).name}"

            if report.image_path

            else None

        ),

        "video_url": (

            f"/uploads/{Path(report.video_path).name}"

            if report.video_path

            else None

        ),

        # --------------------------------------------------
        # VERIFICATION
        # --------------------------------------------------

        "status": report.status,

        "verified_at": report.verified_at,

        # --------------------------------------------------
        # OFFLINE SYNCHRONIZATION
        # --------------------------------------------------

        "client_report_id": report.client_report_id,

        "is_offline_report": report.is_offline_report,

        "offline_created_at": report.offline_created_at,

        "synced_at": report.synced_at,

        # --------------------------------------------------
        # SERVER TIMESTAMP
        # --------------------------------------------------

        "created_at": report.created_at,

    }


# ==========================================================
# CREATE REPORT
# ==========================================================

@router.post("")

def create_report(

    report_type: str = Form(...),

    latitude: float = Form(...),

    longitude: float = Form(...),

    description: str = Form(default=""),

    severity: str = Form(default="MODERATE"),

    image: UploadFile | None = File(
        default=None
    ),

    video: UploadFile | None = File(
        default=None
    ),

    db: Session = Depends(get_db),

    user: User = Depends(
        get_current_user
    ),

):

    """
    Create a citizen or field officer report.

    The report is automatically linked
    to the nearest monitored location.
    """

    # ------------------------------------------------------
    # VALIDATE REPORT TYPE
    # ------------------------------------------------------

    report_type = report_type.strip().upper()

    if report_type not in REPORT_TYPES:

        raise HTTPException(

            status_code=422,

            detail=(

                f"report_type must be one of "

                f"{REPORT_TYPES}"

            ),

        )

    # ------------------------------------------------------
    # VALIDATE SEVERITY
    # ------------------------------------------------------

    severity = severity.strip().upper()

    if severity not in SEVERITY_LEVELS:

        raise HTTPException(

            status_code=422,

            detail=(

                f"severity must be one of "

                f"{SEVERITY_LEVELS}"

            ),

        )

    # ------------------------------------------------------
    # VALIDATE COORDINATES
    # ------------------------------------------------------

    if not (

        -90 <= latitude <= 90

        and

        -180 <= longitude <= 180

    ):

        raise HTTPException(

            status_code=422,

            detail="Invalid coordinates",

        )

    # ------------------------------------------------------
    # SAVE IMAGE
    # ------------------------------------------------------

    image_path = None

    if image is not None and image.filename:

        suffix = (

            Path(image.filename)

            .suffix

            .lower()

        )

        if suffix not in ALLOWED_IMAGE_EXTENSIONS:

            raise HTTPException(

                status_code=422,

                detail=(

                    "Only JPG, JPEG or PNG "

                    "images are accepted"

                ),

            )

        content = image.file.read()

        if len(content) > MAX_IMAGE_SIZE_BYTES:

            raise HTTPException(

                status_code=413,

                detail=(

                    "Image exceeds the "

                    "5 MB size limit"

                ),

            )

        UPLOAD_DIR.mkdir(

            parents=True,

            exist_ok=True,

        )

        filename = (

            f"{uuid.uuid4().hex}{suffix}"

        )

        (

            UPLOAD_DIR / filename

        ).write_bytes(content)

        image_path = filename

    # ------------------------------------------------------
    # SAVE VIDEO
    # ------------------------------------------------------

    video_path = None

    if video is not None and video.filename:

        suffix = (

            Path(video.filename)

            .suffix

            .lower()

        )

        if suffix not in ALLOWED_VIDEO_EXTENSIONS:

            raise HTTPException(

                status_code=422,

                detail=(

                    "Only MP4 or WebM "

                    "videos are accepted"

                ),

            )

        content = video.file.read()

        if len(content) > MAX_VIDEO_SIZE_BYTES:

            raise HTTPException(

                status_code=413,

                detail=(

                    "Video exceeds the "

                    "20 MB size limit"

                ),

            )

        UPLOAD_DIR.mkdir(

            parents=True,

            exist_ok=True,

        )

        filename = (

            f"{uuid.uuid4().hex}{suffix}"

        )

        (

            UPLOAD_DIR / filename

        ).write_bytes(content)

        video_path = filename

    # ------------------------------------------------------
    # FIND NEAREST MONITORED LOCATION
    # ------------------------------------------------------

    nearest_location = find_nearest_location(

        db=db,

        latitude=latitude,

        longitude=longitude,

    )

    # ------------------------------------------------------
    # CREATE REPORT
    # ------------------------------------------------------

    report = Report(

        user_id=user.id,

        report_type=report_type,

        description=(

            description or ""

        ).strip(),

        latitude=latitude,

        longitude=longitude,

        image_path=image_path,

        video_path=video_path,

        severity=severity,

        status="PENDING",

        location_id=(

            nearest_location.id

            if nearest_location

            else None

        ),

    )

    db.add(report)

    db.commit()

    db.refresh(report)

    return _out(

        report,

        reporter=user,

        location=nearest_location,

    )


# ==========================================================
# OFFLINE REPORT SYNCHRONIZATION
# ==========================================================

@router.post("/sync")

def sync_offline_report(

    payload: OfflineReportSync,

    db: Session = Depends(get_db),

    user: User = Depends(
        get_current_user
    ),

):

    """
    Synchronize a report created while
    the device was offline.

    The client_report_id prevents
    duplicate reports.
    """

    # ------------------------------------------------------
    # CHECK FOR DUPLICATE
    # ------------------------------------------------------

    existing = (

        db.query(Report)

        .filter(

            Report.client_report_id

            ==

            payload.client_report_id

        )

        .first()

    )

    if existing:

        # Get the original reporter

        reporter = None

        if existing.user_id:

            reporter = db.get(

                User,

                existing.user_id,

            )

        # Get linked monitored location

        location = None

        if existing.location_id:

            location = db.get(

                Location,

                existing.location_id,

            )

        return {

            "success": True,

            "synced": False,

            "duplicate": True,

            "report": _out(

                existing,

                reporter=reporter,

                location=location,

            ),

        }

    # ------------------------------------------------------
    # VALIDATE REPORT TYPE
    # ------------------------------------------------------

    report_type = (

        payload.report_type

        .strip()

        .upper()

    )

    if report_type not in REPORT_TYPES:

        raise HTTPException(

            status_code=422,

            detail=(

                f"report_type must be one of "

                f"{REPORT_TYPES}"

            ),

        )

    # ------------------------------------------------------
    # VALIDATE COORDINATES
    # ------------------------------------------------------

    if not (

        -90 <= payload.latitude <= 90

        and

        -180 <= payload.longitude <= 180

    ):

        raise HTTPException(

            status_code=422,

            detail="Invalid coordinates",

        )

    # ------------------------------------------------------
    # VALIDATE SEVERITY
    # ------------------------------------------------------

    severity = (

        payload.severity

        .strip()

        .upper()

    )

    if severity not in SEVERITY_LEVELS:

        raise HTTPException(

            status_code=422,

            detail=(

                f"severity must be one of "

                f"{SEVERITY_LEVELS}"

            ),

        )

    # ------------------------------------------------------
    # FIND NEAREST MONITORED LOCATION
    # ------------------------------------------------------

    nearest_location = find_nearest_location(

        db=db,

        latitude=payload.latitude,

        longitude=payload.longitude,

    )

    # ------------------------------------------------------
    # CREATE OFFLINE REPORT
    # ------------------------------------------------------

    report = Report(

        client_report_id=payload.client_report_id,

        user_id=user.id,

        report_type=report_type,

        description=(

            payload.description or ""

        ).strip(),

        latitude=payload.latitude,

        longitude=payload.longitude,

        severity=severity,

        status="PENDING",

        location_id=(

            nearest_location.id

            if nearest_location

            else None

        ),

        is_offline_report=True,

        offline_created_at=(

            payload.offline_created_at

        ),

        synced_at=utcnow(),

    )

    db.add(report)

    db.commit()

    db.refresh(report)

    # ------------------------------------------------------
    # SUCCESS RESPONSE
    # ------------------------------------------------------

    return {

        "success": True,

        "synced": True,

        "duplicate": False,

        "report": _out(

            report,

            reporter=user,

            location=nearest_location,

        ),

    }


# ==========================================================
# LIST REPORTS
# ==========================================================

@router.get("")

def list_reports(

    status: str | None = Query(
        default=None
    ),

    report_type: str | None = Query(
        default=None
    ),

    severity: str | None = Query(
        default=None
    ),

    limit: int = Query(

        default=200,

        ge=1,

        le=1000,

    ),

    db: Session = Depends(
        get_db
    ),

):

    """
    Get reports.

    Optional filters:

    - status
    - report_type
    - severity
    """

    query = db.query(Report)

    # ------------------------------------------------------
    # FILTER BY STATUS
    # ------------------------------------------------------

    if status:

        query = query.filter(

            Report.status

            ==

            status.upper()

        )

    # ------------------------------------------------------
    # FILTER BY REPORT TYPE
    # ------------------------------------------------------

    if report_type:

        query = query.filter(

            Report.report_type

            ==

            report_type.upper()

        )

    # ------------------------------------------------------
    # FILTER BY SEVERITY
    # ------------------------------------------------------

    if severity:

        query = query.filter(

            Report.severity

            ==

            severity.upper()

        )

    # ------------------------------------------------------
    # GET REPORTS
    # ------------------------------------------------------

    rows = (

        query

        .order_by(

            Report.created_at.desc()

        )

        .limit(limit)

        .all()

    )

    # ------------------------------------------------------
    # LOAD USERS
    # ------------------------------------------------------

    users = {

        user.id: user

        for user in db.query(User).all()

    }

    # ------------------------------------------------------
    # LOAD LOCATIONS
    # ------------------------------------------------------

    locations = {

        location.id: location

        for location in db.query(Location).all()

    }

    # ------------------------------------------------------
    # FORMAT OUTPUT
    # ------------------------------------------------------

    return [

        _out(

            report,

            reporter=users.get(

                report.user_id

            ),

            location=locations.get(

                report.location_id

            ),

        )

        for report in rows

    ]


# ==========================================================
# VERIFY REPORT
# ==========================================================

@router.put("/{report_id}/verify")

def verify_report(

    report_id: int,

    payload: ReportVerify,

    db: Session = Depends(
        get_db
    ),

    user: User = Depends(
        get_current_user
    ),

):

    """
    Verify or reject a citizen report.

    Only ADMIN and FIELD_OFFICER
    users can perform verification.
    """

    # ------------------------------------------------------
    # ROLE CHECK
    # ------------------------------------------------------

    if user.role not in (

        "ADMIN",

        "FIELD_OFFICER",

    ):

        raise HTTPException(

            status_code=403,

            detail=(

                "Only officers can "

                "verify reports"

            ),

        )

    # ------------------------------------------------------
    # FIND REPORT
    # ------------------------------------------------------

    report = db.get(

        Report,

        report_id,

    )

    if not report:

        raise HTTPException(

            status_code=404,

            detail="Report not found",

        )

    # ------------------------------------------------------
    # UPDATE STATUS
    # ------------------------------------------------------

    report.status = (

        payload.status

        .upper()

    )

    report.verified_at = utcnow()

    db.commit()

    db.refresh(report)

    # ------------------------------------------------------
    # GET REPORTER
    # ------------------------------------------------------

    reporter = None

    if report.user_id:

        reporter = db.get(

            User,

            report.user_id,

        )

    # ------------------------------------------------------
    # GET LINKED LOCATION
    # ------------------------------------------------------

    location = None

    if report.location_id:

        location = db.get(

            Location,

            report.location_id,

        )

    return _out(

        report,

        reporter=reporter,

        location=location,

    )


# ==========================================================
# GET SINGLE REPORT
# ==========================================================

@router.get("/{report_id}")

def get_report(

    report_id: int,

    db: Session = Depends(
        get_db
    ),

):

    """
    Get one citizen or field report.
    """

    # ------------------------------------------------------
    # FIND REPORT
    # ------------------------------------------------------

    report = db.get(

        Report,

        report_id,

    )

    if not report:

        raise HTTPException(

            status_code=404,

            detail="Report not found",

        )

    # ------------------------------------------------------
    # GET REPORTER
    # ------------------------------------------------------

    reporter = None

    if report.user_id:

        reporter = db.get(

            User,

            report.user_id,

        )

    # ------------------------------------------------------
    # GET LINKED LOCATION
    # ------------------------------------------------------

    location = None

    if report.location_id:

        location = db.get(

            Location,

            report.location_id,

        )

    # ------------------------------------------------------
    # RETURN REPORT
    # ------------------------------------------------------

    return _out(

        report,

        reporter=reporter,

        location=location,

    )