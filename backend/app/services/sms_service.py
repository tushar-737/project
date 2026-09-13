"""Multilingual simulated SMS dispatch.

HIGH and CRITICAL alerts generate SMS logs.

The service supports multiple languages and is designed so that
a real SMS provider such as MSG91, Twilio, or a government
emergency notification gateway can be integrated later.
"""

from sqlalchemy.orm import Session

from ..models import SmsLog


# ==========================================================
# SUPPORTED LANGUAGES
# ==========================================================

SUPPORTED_LANGUAGES = {
    "EN": "English",
    "HI": "Hindi",
    "AS": "Assamese",
    "BN": "Bengali",
}


# ==========================================================
# MULTILINGUAL SMS MESSAGE BUILDER
# ==========================================================

def build_sms_message(
    location,
    risk_level: str,
    risk_score: float,
    language: str = "EN",
) -> str:
    """
    Build a short landslide warning message
    in the requested language.
    """

    language = language.upper()

    score = f"{risk_score:.0f}/100"

    # ------------------------------------------------------
    # ENGLISH
    # ------------------------------------------------------

    if language == "EN":
        return (
            f"LANDSLIDE WARNING: {risk_level} risk "
            f"({score}) near {location.name}, "
            f"{location.district}. "
            f"Avoid vulnerable roads and remain alert."
        )

    # ------------------------------------------------------
    # HINDI
    # ------------------------------------------------------

    if language == "HI":
        return (
            f"भूस्खलन चेतावनी: {location.name}, "
            f"{location.district} के पास "
            f"{risk_level} जोखिम ({score}) पाया गया है। "
            f"संवेदनशील सड़कों से बचें और सतर्क रहें।"
        )

    # ------------------------------------------------------
    # ASSAMESE
    # ------------------------------------------------------

    if language == "AS":
        return (
            f"ভূমিস্খলন সতৰ্কবাণী: {location.name}, "
            f"{location.district}ৰ ওচৰত "
            f"{risk_level} বিপদ ({score}) ধৰা পৰিছে। "
            f"বিপদজনক পথ এৰাই চলক আৰু সতৰ্ক থাকক।"
        )

    # ------------------------------------------------------
    # BENGALI
    # ------------------------------------------------------

    if language == "BN":
        return (
            f"ভূমিধস সতর্কতা: {location.name}, "
            f"{location.district} এর কাছে "
            f"{risk_level} ঝুঁকি ({score}) শনাক্ত হয়েছে। "
            f"ঝুঁকিপূর্ণ রাস্তা এড়িয়ে চলুন এবং সতর্ক থাকুন।"
        )

    # ------------------------------------------------------
    # FALLBACK TO ENGLISH
    # ------------------------------------------------------

    return (
        f"LANDSLIDE WARNING: {risk_level} risk "
        f"({score}) near {location.name}, "
        f"{location.district}. "
        f"Avoid vulnerable roads and remain alert."
    )


# ==========================================================
# SEND ALERT SMS
# ==========================================================

def send_alert_sms(
    db: Session,
    location,
    risk_level: str,
    risk_score: float,
    message: str,
    language: str = "EN",
) -> SmsLog:
    """
    Log a simulated multilingual SMS broadcast.

    A real SMS gateway can later replace this implementation
    without changing the alert engine.
    """

    # ------------------------------------------------------
    # VALIDATE LANGUAGE
    # ------------------------------------------------------

    language = language.upper()

    if language not in SUPPORTED_LANGUAGES:
        language = "EN"

    # ------------------------------------------------------
    # RECIPIENT ESTIMATE
    # ------------------------------------------------------

    recipients = max(
        5,
        min(
            200,
            int(
                round(
                    (location.population_factor or 0.5)
                    * 10
                    * 20
                )
            ),
        ),
    )

    # ------------------------------------------------------
    # BUILD MULTILINGUAL MESSAGE
    # ------------------------------------------------------

    sms_message = build_sms_message(
        location=location,
        risk_level=risk_level,
        risk_score=risk_score,
        language=language,
    )

    # ------------------------------------------------------
    # CREATE SMS LOG
    # ------------------------------------------------------

    sms = SmsLog(
        location_id=location.id,

        recipient_area=(
            f"{location.district} District, "
            f"{location.state}"
        ),

        phone_recipients=recipients,

        message=sms_message,

        channel=f"SIMULATED_SMS_{language}",

        status="SENT",
    )

    db.add(sms)

    db.flush()

    return sms