"""
NER LandslideAI - Satellite Intelligence Service

Satellite intelligence layer for landslide monitoring.

Data flow:

    Real Sentinel-2 Satellite Data
                ↓
          NDVI Calculation
                ↓
      Satellite Intelligence

If real satellite data is unavailable:

      Environmental Data
                ↓
      Environmental Proxy
                ↓
      Satellite Intelligence
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .satellite_provider import get_real_satellite_observation


# ============================================================
# SATELLITE INTELLIGENCE RESULT
# ============================================================

@dataclass
class SatelliteData:

    vegetation_index: float
    surface_wetness: float

    vegetation_risk: float
    wetness_risk: float
    satellite_risk: float

    source: str
    status: str
    data_mode: str

    observation_date: Optional[str] = None
    cloud_cover: Optional[float] = None

    raw_ndvi: Optional[float] = None
    observation_age_days: Optional[int] = None
    freshness_status: Optional[str] = None


    def as_dict(self) -> dict:

        return {

            "vegetation_index": self.vegetation_index,

            "surface_wetness": self.surface_wetness,

            "vegetation_risk": self.vegetation_risk,

            "wetness_risk": self.wetness_risk,

            "satellite_risk": self.satellite_risk,

            "source": self.source,

            "status": self.status,

            "data_mode": self.data_mode,

            "observation_date": self.observation_date,

            "cloud_cover": self.cloud_cover,

            "raw_ndvi": self.raw_ndvi,

            "observation_age_days": self.observation_age_days,

            "freshness_status": self.freshness_status,
        }


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:

    """
    Keep a numeric value inside a valid range.
    """

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


# ============================================================
# CALCULATE SATELLITE RISK
# ============================================================

def calculate_satellite_risk(
    vegetation_index: float,
    surface_wetness: float,
) -> tuple[float, float, float]:

    """
    Calculate satellite intelligence risk.

    vegetation_index:

        0.0 = Very poor vegetation

        1.0 = Healthy vegetation


    surface_wetness:

        0.0 = Dry

        1.0 = Very wet
    """

    vegetation_index = clamp(
        vegetation_index,
        0.0,
        1.0,
    )

    surface_wetness = clamp(
        surface_wetness,
        0.0,
        1.0,
    )


    # Lower vegetation coverage can increase
    # landslide susceptibility.

    vegetation_risk = (
        1.0 - vegetation_index
    ) * 100


    # Higher wetness increases soil saturation.

    wetness_risk = (
        surface_wetness
    ) * 100


    # Wetness receives higher importance.

    satellite_risk = (
        vegetation_risk * 0.40
        +
        wetness_risk * 0.60
    )


    satellite_risk = clamp(
        satellite_risk,
        0.0,
        100.0,
    )


    return (

        round(
            vegetation_risk,
            2,
        ),

        round(
            wetness_risk,
            2,
        ),

        round(
            satellite_risk,
            2,
        ),
    )


# ============================================================
# GET RISK STATUS
# ============================================================

def get_risk_status(
    satellite_risk: float,
) -> str:

    """
    Convert numeric risk into severity.
    """

    if satellite_risk < 25:

        return "LOW"

    elif satellite_risk < 50:

        return "MODERATE"

    elif satellite_risk < 75:

        return "HIGH"

    return "CRITICAL"


# ============================================================
# ENVIRONMENTAL FALLBACK
# ============================================================

def generate_environmental_fallback(
    location,
    rainfall_24h: float,
    rainfall_72h: float,
    soil_moisture: float,
) -> tuple[float, float]:

    """
    Generate environmental proxy indicators.

    IMPORTANT:

    These are NOT real satellite observations.

    They are used only when Sentinel-2 data
    is unavailable.
    """

    rainfall_24h = max(
        0.0,
        rainfall_24h,
    )

    rainfall_72h = max(
        0.0,
        rainfall_72h,
    )

    soil_moisture = clamp(
        soil_moisture,
        0.0,
        100.0,
    )


    slope_angle = max(
        0.0,
        float(
            location.slope_angle
            or 0.0
        ),
    )


    # ========================================================
    # VEGETATION PROXY
    # ========================================================

    vegetation_index = 0.75


    if slope_angle >= 40:

        vegetation_index -= 0.20

    elif slope_angle >= 30:

        vegetation_index -= 0.12

    elif slope_angle >= 20:

        vegetation_index -= 0.05


    if rainfall_72h >= 150:

        vegetation_index -= 0.15

    elif rainfall_72h >= 75:

        vegetation_index -= 0.08


    vegetation_index = clamp(
        vegetation_index,
        0.0,
        1.0,
    )


    # ========================================================
    # SURFACE WETNESS PROXY
    # ========================================================

    rainfall_component = min(
        rainfall_72h / 200.0,
        1.0,
    )


    soil_component = (
        soil_moisture / 100.0
    )


    surface_wetness = (

        rainfall_component * 0.50

        +

        soil_component * 0.50
    )


    surface_wetness = clamp(
        surface_wetness,
        0.0,
        1.0,
    )


    return (
        vegetation_index,
        surface_wetness,
    )


# ============================================================
# CALCULATE SURFACE WETNESS
# ============================================================

def calculate_surface_wetness(
    rainfall_72h: float,
    soil_moisture: float,
) -> float:

    """
    Calculate surface wetness using
    environmental information.

    Future versions can use:

    - Sentinel-1 SAR
    - Satellite soil moisture
    - Surface water products
    """

    rainfall_72h = max(
        0.0,
        rainfall_72h,
    )


    soil_moisture = clamp(
        soil_moisture,
        0.0,
        100.0,
    )


    rainfall_component = min(
        rainfall_72h / 200.0,
        1.0,
    )


    soil_component = (
        soil_moisture / 100.0
    )


    surface_wetness = (

        rainfall_component * 0.50

        +

        soil_component * 0.50
    )


    return clamp(
        surface_wetness,
        0.0,
        1.0,
    )


# ============================================================
# MAIN SATELLITE INTELLIGENCE
# ============================================================

def get_satellite_intelligence(

    location,

    rainfall_24h: float = 0.0,

    rainfall_72h: float = 0.0,

    soil_moisture: float = 0.0,

) -> SatelliteData:

    """
    Get satellite intelligence for a monitored location.

    Priority:

    1. Real Sentinel-2 observation

    2. Environmental fallback
    """


    # ========================================================
    # TRY REAL SENTINEL-2 DATA
    # ========================================================

    real_observation = (
        get_real_satellite_observation(

            latitude=float(
                location.latitude
            ),

            longitude=float(
                location.longitude
            ),

        )
    )


    # ========================================================
    # REAL SATELLITE MODE
    # ========================================================

    if real_observation is not None:


        vegetation_index = (
            real_observation.vegetation_index
        )


        # NDVI comes from real Sentinel-2 imagery.
        #
        # Wetness currently uses environmental
        # information.

        surface_wetness = (
            calculate_surface_wetness(

                rainfall_72h=rainfall_72h,

                soil_moisture=soil_moisture,

            )
        )


        source = (
            real_observation.source
        )


        data_mode = (
            "REAL_SATELLITE"
        )


        observation_date = (
            real_observation.observation_date
        )


        cloud_cover = (
            real_observation.cloud_cover
        )


        raw_ndvi = (
            getattr(
                real_observation,
                "raw_ndvi",
                None,
            )
        )


        observation_age_days = (
            getattr(
                real_observation,
                "observation_age_days",
                None,
            )
        )


        freshness_status = (
            getattr(
                real_observation,
                "freshness_status",
                None,
            )
        )


    # ========================================================
    # ENVIRONMENTAL FALLBACK
    # ========================================================

    else:


        (
            vegetation_index,
            surface_wetness,
        ) = generate_environmental_fallback(

            location=location,

            rainfall_24h=rainfall_24h,

            rainfall_72h=rainfall_72h,

            soil_moisture=soil_moisture,

        )


        source = (
            "ENVIRONMENTAL_PROXY"
        )


        data_mode = (
            "ENVIRONMENTAL_FALLBACK"
        )


        observation_date = None

        cloud_cover = None

        raw_ndvi = None

        observation_age_days = None

        freshness_status = (
            "NO_REAL_OBSERVATION"
        )


    # ========================================================
    # CALCULATE SATELLITE RISK
    # ========================================================

    (
        vegetation_risk,
        wetness_risk,
        satellite_risk,
    ) = calculate_satellite_risk(

        vegetation_index=vegetation_index,

        surface_wetness=surface_wetness,

    )


    # ========================================================
    # GET STATUS
    # ========================================================

    status = get_risk_status(
        satellite_risk
    )


    # ========================================================
    # RETURN RESULT
    # ========================================================

    return SatelliteData(

        vegetation_index=round(
            vegetation_index,
            3,
        ),

        surface_wetness=round(
            surface_wetness,
            3,
        ),

        vegetation_risk=vegetation_risk,

        wetness_risk=wetness_risk,

        satellite_risk=satellite_risk,

        source=source,

        status=status,

        data_mode=data_mode,

        observation_date=observation_date,

        cloud_cover=cloud_cover,

        raw_ndvi=raw_ndvi,

        observation_age_days=observation_age_days,

        freshness_status=freshness_status,

    )