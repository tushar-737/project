"""Simulated SMS dispatch.

Every HIGH/CRITICAL alert generates an SMS log row exactly as a real
gateway integration would. Swapping in a paid provider later only changes
`send_alert_sms`:

    Twilio:   client.messages.create(to="+91...", from_=TWILIO_NUMBER,
                                     body=message)
    MSG91 / Government gateway: HTTP POST of message + recipient list

The database logging and message format stay identical.
"""
from sqlalchemy.orm import Session

from ..models import SmsLog


def send_alert_sms(db: Session, location, risk_level: str, risk_score: float,
                   message: str) -> SmsLog:
    """Log a simulated SMS broadcast to the affected district.

    Recipient count is a coarse population estimate (prototype): 10 SMS per
    population factor point, capped at 200.
    """
    recipients = max(5, min(200, int(round((location.population_factor or 0.5) * 10 * 20))))

    sms = SmsLog(
        location_id=location.id,
        recipient_area=f"{location.district} District, {location.state}",
        phone_recipients=recipients,
        message=f"LANDSLIDE WARNING: {risk_level} landslide risk "
                f"({risk_score:.0f}/100) detected near {location.name}. "
                "Avoid vulnerable roads.",
        channel="SIMULATED_SMS",
        status="SENT",
    )
    db.add(sms)
    db.flush()
    return sms
