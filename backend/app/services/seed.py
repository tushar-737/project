"""Automatic seed of realistic demo data across all 8 North Eastern states.

Runs once when the database is first created (see main.py lifespan):

    - 27 vulnerable locations (Assam, Arunachal Pradesh, Meghalaya, Manipur,
      Mizoram, Nagaland, Tripura, Sikkim) with realistic coordinates,
      elevation and slope
    - 3 demo users (admin / field officer / citizen)
    - 10 monitored road corridors with current statuses
    - Historical environmental + risk samples for the risk-trend chart
    - A current-state simulation for every location through the automatic
      pipeline (env -> risk engine -> alert -> SMS -> emergency priority)
    - Citizen/field reports in all report categories
"""
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..ml.risk_engine import RiskFeatures, get_risk_engine
from ..models import (
    Alert,
    EnvironmentalData,
    Location,
    Report,
    RiskPrediction,
    Road,
    SmsLog,
    User,
)
from ..utils.security import hash_password
from .emergency_service import ROAD_ISOLATION_SCORE, compute_all_priorities
from .sensor_service import SimulatedSensorService

# (name, district, state, lat, lon, elevation_m, slope_deg, hist, population, isolation)
LOCATIONS = [
    # Meghalaya
    ("Shillong", "East Khasi Hills", "Meghalaya", 25.5788, 91.8933, 1496, 30, 0.60, 0.75, 0.35),
    ("Cherrapunji", "East Khasi Hills", "Meghalaya", 25.2704, 91.7283, 1484, 28, 0.75, 0.45, 0.50),
    ("Mawsynram", "East Khasi Hills", "Meghalaya", 25.2993, 91.5821, 1400, 32, 0.80, 0.30, 0.60),
    ("Tura", "West Garo Hills", "Meghalaya", 25.5142, 90.2026, 657, 22, 0.40, 0.55, 0.40),
    # Assam
    ("Haflong", "Dima Hasao", "Assam", 25.1647, 93.0174, 680, 25, 0.50, 0.50, 0.60),
    ("Guwahati Hill Region", "Kamrup Metro", "Assam", 26.1445, 91.7362, 240, 18, 0.35, 0.90, 0.15),
    ("Diphu", "Karbi Anglong", "Assam", 25.8434, 93.4283, 186, 20, 0.35, 0.60, 0.30),
    ("Jatinga", "Dima Hasao", "Assam", 25.4439, 93.0399, 560, 26, 0.55, 0.25, 0.65),
    # Arunachal Pradesh
    ("Itanagar", "Papum Pare", "Arunachal Pradesh", 27.0844, 93.6053, 750, 28, 0.45, 0.85, 0.25),
    ("Bomdila", "West Kameng", "Arunachal Pradesh", 27.2660, 92.4214, 2417, 33, 0.55, 0.35, 0.60),
    ("Aalo", "West Siang", "Arunachal Pradesh", 28.1757, 94.7802, 302, 22, 0.40, 0.50, 0.55),
    ("Tawang", "Tawang", "Arunachal Pradesh", 27.5854, 91.8602, 2669, 35, 0.50, 0.35, 0.70),
    # Nagaland
    ("Kohima", "Kohima", "Nagaland", 25.6751, 94.1086, 1444, 36, 0.65, 0.80, 0.40),
    ("Dimapur", "Dimapur", "Nagaland", 25.9111, 93.7437, 260, 15, 0.30, 0.80, 0.20),
    ("Phek", "Phek", "Nagaland", 25.6606, 94.4573, 1524, 32, 0.55, 0.45, 0.65),
    # Manipur
    ("Imphal", "Imphal West", "Manipur", 24.8170, 93.9368, 786, 14, 0.25, 0.85, 0.25),
    ("Ukhrul", "Ukhrul", "Manipur", 25.1100, 94.3580, 1662, 34, 0.60, 0.45, 0.70),
    ("Churachandpur", "Churachandpur", "Manipur", 24.3343, 93.6909, 914, 26, 0.50, 0.60, 0.60),
    # Mizoram
    ("Aizawl", "Aizawl", "Mizoram", 23.7271, 92.7176, 1132, 38, 0.70, 0.85, 0.45),
    ("Lunglei", "Lunglei", "Mizoram", 22.8866, 92.7248, 722, 30, 0.55, 0.50, 0.60),
    ("Champhai", "Champhai", "Mizoram", 23.4560, 93.3291, 1417, 32, 0.60, 0.45, 0.65),
    ("Serchhip", "Serchhip", "Mizoram", 23.2984, 92.8480, 914, 30, 0.55, 0.35, 0.70),
    # Tripura
    ("Ambassa", "Dhalai", "Tripura", 23.9260, 91.8450, 180, 16, 0.30, 0.45, 0.50),
    ("Jampui Hills", "North Tripura", "Tripura", 24.0067, 92.2579, 930, 26, 0.50, 0.20, 0.75),
    # Sikkim
    ("Gangtok", "East Sikkim", "Sikkim", 27.3389, 88.6065, 1650, 37, 0.65, 0.80, 0.50),
    ("Namchi", "South Sikkim", "Sikkim", 27.1659, 88.3508, 1315, 30, 0.55, 0.50, 0.55),
    ("Mangan", "North Sikkim", "Sikkim", 27.5207, 88.5340, 956, 28, 0.50, 0.35, 0.80),
]

# Current weather scenario simulated per location at seed time.
# Calibrated against the deterministic engine + RNG (seed 20240908) so every
# fresh database reproduces the same monsoon snapshot across all 8 states:
#   7 CRITICAL / 5 HIGH / 13 MODERATE / 2 LOW sites.
SEED_SCENARIOS = {
    # EXTREME_RAIN -> CRITICAL band
    1: "EXTREME_RAIN",   # Shillong, Meghalaya
    2: "EXTREME_RAIN",   # Cherrapunji, Meghalaya
    3: "EXTREME_RAIN",   # Mawsynram, Meghalaya
    13: "EXTREME_RAIN",  # Kohima, Nagaland
    17: "EXTREME_RAIN",  # Ukhrul, Manipur
    19: "EXTREME_RAIN",  # Aizawl, Mizoram
    25: "EXTREME_RAIN",  # Gangtok, Sikkim
    # HEAVY_RAIN -> HIGH band
    4: "HEAVY_RAIN",     # Tura, Meghalaya
    6: "HEAVY_RAIN",     # Guwahati Hill Region, Assam
    7: "HEAVY_RAIN",     # Diphu, Assam
    11: "HEAVY_RAIN",    # Aalo, Arunachal Pradesh
    # MODERATE_RAIN / NORMAL -> MODERATE band
    5: "MODERATE_RAIN",  # Haflong, Assam
    8: "MODERATE_RAIN",  # Jatinga, Assam
    9: "MODERATE_RAIN",  # Itanagar, Arunachal Pradesh
    10: "NORMAL",        # Bomdila, Arunachal Pradesh
    12: "MODERATE_RAIN", # Tawang, Arunachal Pradesh
    15: "NORMAL",        # Phek, Nagaland
    18: "MODERATE_RAIN", # Churachandpur, Manipur
    20: "MODERATE_RAIN", # Lunglei, Mizoram
    21: "NORMAL",        # Champhai, Mizoram
    22: "NORMAL",        # Serchhip, Mizoram
    24: "MODERATE_RAIN", # Jampui Hills, Tripura
    26: "NORMAL",        # Namchi, Sikkim
    27: "MODERATE_RAIN", # Mangan, Sikkim
    # NORMAL -> LOW band (stable low-slope sites)
    14: "NORMAL",        # Dimapur, Nagaland
    16: "NORMAL",        # Imphal, Manipur
    23: "NORMAL",        # Ambassa, Tripura
}

# Locations that carry a multi-day risk history (analytics trend chart).
TREND_LOCATIONS = [1, 13, 19, 25, 6, 17]
TREND_SCENARIOS = ["NORMAL", "MODERATE_RAIN", "MODERATE_RAIN", "HEAVY_RAIN", "HEAVY_RAIN"]
TREND_HOURS_AGO = [42, 36, 24, 18, 6]

# (name, district, state, lat, lon, end_lat, end_lon, status, risk, location_idx_1based)
ROADS = [
    ("NH-6 Shillong-Guwahati Rd", "East Khasi Hills", "Meghalaya", 25.5788, 91.8933, 25.92, 91.86, "PARTIALLY_BLOCKED", "HIGH", 1),
    ("Aizawl-Lengpui Airport Rd", "Aizawl", "Mizoram", 23.7271, 92.7176, 23.8320, 92.6160, "BLOCKED", "CRITICAL", 19),
    ("NH-29 Kohima-Dimapur Rd", "Kohima", "Nagaland", 25.6751, 94.1086, 25.8200, 93.9200, "PARTIALLY_BLOCKED", "HIGH", 13),
    ("Gangtok-Nathula Border Rd", "East Sikkim", "Sikkim", 27.3389, 88.6065, 27.3862, 88.7927, "OPEN", "MODERATE", 25),
    ("Itanagar-Banderdewa Rd", "Papum Pare", "Arunachal Pradesh", 27.0844, 93.6053, 27.0600, 93.4300, "HIGH_RISK", "HIGH", 9),
    ("Ukhrul-Imphal Rd", "Ukhrul", "Manipur", 25.1100, 94.3580, 24.8600, 94.1000, "PARTIALLY_BLOCKED", "HIGH", 17),
    ("Cherrapunji-Shella Rd", "East Khasi Hills", "Meghalaya", 25.2704, 91.7283, 25.2000, 91.6700, "BLOCKED", "CRITICAL", 2),
    ("Lunglei-Tlabung Rd", "Lunglei", "Mizoram", 22.8866, 92.7248, 22.9500, 92.5800, "HIGH_RISK", "MODERATE", 20),
    ("NH-27 Haflong-Silchar Rd", "Dima Hasao", "Assam", 25.1647, 93.0174, 24.9000, 92.9800, "OPEN", "MODERATE", 5),
    ("Bomdila-Dirang Rd", "West Kameng", "Arunachal Pradesh", 27.2660, 92.4214, 27.3600, 92.2500, "OPEN", "HIGH", 10),
]

REPORTS = [
    ("LANDSLIDE", "Fresh landslide debris covering half the road near 11th Mile, NH-6.", 25.6100, 91.8700, "PENDING", 1),
    ("ROAD_BLOCKAGE", "Boulders and mud fully block the Aizawl-Lengpui road near Sairang.", 23.7900, 92.6600, "VERIFIED", 2),
    ("ROAD_CRACK", "Wide transverse cracks developing on the Kohima-Dimapur highway.", 25.7700, 93.9500, "PENDING", 3),
    ("SLOPE_CRACK", "Visible tension cracks along hill slope above Jatinga hamlet.", 25.4600, 93.0500, "PENDING", 4),
    ("SLOPE_MOVEMENT", "Slow downhill creep observed on slope behind PHC in Bomdila.", 27.2700, 92.4300, "VERIFIED", 5),
    ("ROCKFALL", "Rockfall near Aizawl - frequent small boulders on carriageway.", 23.7600, 92.6900, "PENDING", 6),
    ("FLOODING", "Water logging at road underpass; minor slides on embankment.", 25.9300, 93.7100, "REJECTED", 7),
    ("ROAD_CRACK", "Cracks on Gangtok-Nathula road surface near 12th Mile.", 27.3500, 88.6800, "PENDING", 8),
    ("LANDSLIDE", "Slope failure 200 m east of Ukhrul town bazaar.", 25.1200, 94.3600, "PENDING", 9),
    ("FLOODING", "Flash flood washed out culvert approach near Ambassa.", 23.9300, 91.8500, "PENDING", 10),
]

REPORT_TYPES = ["LANDSLIDE", "ROAD_BLOCKAGE", "ROAD_CRACK", "SLOPE_CRACK",
                "SLOPE_MOVEMENT", "ROCKFALL", "FLOODING"]


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _ago(hours: float) -> datetime:
    return _now() - timedelta(hours=hours)


def _insert_history(db: Session, engine, sensor: SimulatedSensorService,
                    location: Location):
    """Insert environmental + risk rows for the last ~2 days (trend chart)."""
    hist: list[EnvironmentalData] = []
    preds: list[RiskPrediction] = []
    for scenario, hours in zip(TREND_SCENARIOS, TREND_HOURS_AGO):
        sample = sensor.read(location, scenario=scenario)
        env = EnvironmentalData(
            location_id=location.id,
            rainfall=sample.rainfall, soil_moisture=sample.soil_moisture,
            temperature=sample.temperature, humidity=sample.humidity,
            slope_angle=sample.slope_angle, scenario=sample.scenario,
            timestamp=_ago(hours),
        )
        result = engine.predict(
            RiskFeatures(
                rainfall=env.rainfall, soil_moisture=env.soil_moisture,
                slope_angle=env.slope_angle, elevation=location.elevation,
                historical_factor=location.historical_landslide_factor,
                humidity=env.humidity,
            )
        )
        hist.append(env)
        preds.append(RiskPrediction(
            location_id=location.id,
            risk_score=result.score, risk_level=result.level,
            confidence=result.confidence,
            contributing_factors=json.dumps(result.factors),
            prediction_time=env.timestamp,
        ))
    db.add_all(hist)
    db.add_all(preds)


def seed_database(db: Session) -> None:
    """Seed the full demo dataset. Safe to call only on an empty database."""
    engine = get_risk_engine()
    # Deterministic random source: every fresh database gets the same
    # balanced demo dataset (important for repeatable demonstrations).
    sensor = SimulatedSensorService(seed=20240908)

    # ------------------------------------------------------------------ users
    users = {
        "admin": User(name="Admin Officer", email="admin@ner.gov.in",
                      password_hash=hash_password("admin123"), role="ADMIN"),
        "officer": User(name="Field Officer", email="officer@ner.gov.in",
                        password_hash=hash_password("officer123"), role="FIELD_OFFICER"),
        "citizen": User(name="Citizen User", email="citizen@ner.gov.in",
                        password_hash=hash_password("citizen123"), role="CITIZEN"),
    }
    db.add_all(users.values())
    db.flush()

    # ------------------------------------------------------------- locations
    locations: dict[int, Location] = {}
    for i, (name, district, state, lat, lon, elev, slope, hist, pop, iso) in enumerate(LOCATIONS, start=1):
        loc = Location(
            name=name, district=district, state=state,
            latitude=lat, longitude=lon, elevation=elev, slope_angle=slope,
            historical_landslide_factor=hist,
            population_factor=pop, isolation_factor=iso,
        )
        locations[i] = loc
    db.add_all(locations.values())
    db.flush()

    # ----------------------------------------------------- risk history rows
    for idx in TREND_LOCATIONS:
        _insert_history(db, engine, sensor, locations[idx])
    db.flush()

    # ------------------------------------------------- current-state samples
    # Runs the genuine automatic pipeline for every location: sample ->
    # prediction -> alert -> SMS -> emergency priority.
    from .pipeline import run_risk_pipeline

    for idx, scenario in SEED_SCENARIOS.items():
        sample = sensor.read(locations[idx], scenario=scenario)
        run_risk_pipeline(db, locations[idx], sample)
        db.expire_all()  # re-read committed state

    # ---------------------------------------------------------------- roads
    for (name, district, state, lat, lon, elat, elon, status, risk, loc_idx) in ROADS:
        db.add(Road(
            name=name, district=district, state=state,
            latitude=lat, longitude=lon, end_latitude=elat, end_longitude=elon,
            status=status, risk_level=risk, location_id=loc_idx,
            updated_at=_ago(2.0),
        ))
    db.commit()

    # One historical resolved alert + SMS for the "recent alerts" feed.
    first = db.query(Location).order_by(Location.id).first()
    resolved_alert = Alert(
        location_id=first.id, risk_level="HIGH", risk_score=63.0,
        message="LANDSLIDE WARNING\nLocation: Shillong\nRisk Level: HIGH\n"
                "Risk Score: 63/100\nReason: Moderate rainfall and high soil "
                "moisture detected.\nRecommended Action: Avoid vulnerable roads.",
        status="RESOLVED", created_at=_ago(26), resolved_at=_ago(20),
    )
    db.add(resolved_alert)
    db.add(SmsLog(
        location_id=first.id, recipient_area=f"{first.district} District, {first.state}",
        phone_recipients=120,
        message="LANDSLIDE WARNING: HIGH landslide risk (63/100) detected "
                f"near {first.name}. Avoid vulnerable roads.",
        channel="SIMULATED_SMS", status="SENT", created_at=_ago(26),
    ))

    # -------------------------------------------------------------- reports
    officer_ids = [users["officer"].id, users["citizen"].id]
    for i, (rtype, desc, lat, lon, status, _tag) in enumerate(REPORTS, start=1):
        db.add(Report(
            user_id=officer_ids[i % 2],
            report_type=rtype, description=desc,
            latitude=lat, longitude=lon,
            status=status, created_at=_ago(i * 3.0 + 5),
        ))
    db.commit()

    compute_all_priorities(db)
    db.commit()
