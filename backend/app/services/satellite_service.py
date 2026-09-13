"""
NER LandslideAI - Satellite Intelligence Service

This module provides satellite-derived environmental intelligence
for landslide monitoring.

Current prototype:
- Satellite intelligence architecture
- Vegetation condition indicator
- Surface wetness indicator
- Terrain observation context

The service is designed so real satellite sources such as
Sentinel / ISRO-NRSC data can be integrated later without
changing the rest of the application.
"""

from __future__ import annotations

from dataclasses import dataclass


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

    def as_dict(self) -> dict:
        return {
            "vegetation_index": self.vegetation_index,
            "surface_wetness": self.surface_wetness,
            "vegetation_risk": self.vegetation_risk,
            "wetness_risk": self.wetness_risk,
            "satellite_risk": self.satellite_risk,
            "source": self.source,
            "status": self.status,
        }


# ============================================================
# SATELLITE INTELLIGENCE SERVICE
# ============================================================

def get_satellite_intelligence(
    location,
    rainfall_24h: float = 0.0,
    rainfall_72h: float = 0.0,
    soil_moisture: float = 0.0,
) -> SatelliteData:
    """
    Generate satellite intelligence indicators.

    IMPORTANT:
    This prototype keeps the satellite intelligence layer
    independent from the main risk engine.

    It can later be connected to:
    - Sentinel-1 SAR
    - Sentinel-2 optical imagery
    - ISRO / NRSC satellite feeds
    - Google Earth Engine

    Current indicators use environmental conditions to provide
    a prototype satellite observation layer.
    """

    # ========================================================
    # NORMALIZE INPUTS
    # ========================================================

    rainfall_24h = max(0.0, rainfall_24h)
    rainfall_72h = max(0.0, rainfall_72h)

    soil_moisture = max(
        0.0,
        min(100.0, soil_moisture),
    )

    slope_angle = max(
        0.0,
        float(location.slope_angle),
    )

    # ========================================================
    # VEGETATION CONDITION INDICATOR
    # ========================================================
    #
    # Prototype value similar in concept to a normalized
    # vegetation indicator.
    #
    # Higher values = healthier vegetation coverage.
    #

    vegetation_index = 0.75

    # Steeper terrain generally has less stable surface cover.
    if slope_angle >= 40:
        vegetation_index -= 0.20
    elif slope_angle >= 30:
        vegetation_index -= 0.12
    elif slope_angle >= 20:
        vegetation_index -= 0.05

    # Heavy rainfall can indicate disturbed surface conditions.
    if rainfall_72h >= 150:
        vegetation_index -= 0.15
    elif rainfall_72h >= 75:
        vegetation_index -= 0.08

    vegetation_index = max(
        0.0,
        min(1.0, vegetation_index),
    )

    # ========================================================
    # SURFACE WETNESS INDICATOR
    # ========================================================
    #
    # Higher values = wetter surface conditions.
    #

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

    surface_wetness = max(
        0.0,
        min(1.0, surface_wetness),
    )

    # ========================================================
    # VEGETATION RISK
    # ========================================================

    vegetation_risk = (
        1.0 - vegetation_index
    ) * 100

    # ========================================================
    # WETNESS RISK
    # ========================================================

    wetness_risk = (
        surface_wetness * 100
    )

    # ========================================================
    # SATELLITE RISK
    # ========================================================
    #
    # Wetness has higher importance because water saturation
    # is a major landslide trigger.
    #

    satellite_risk = (

        vegetation_risk * 0.40

        +

        wetness_risk * 0.60

    )

    satellite_risk = round(
        max(
            0.0,
            min(
                100.0,
                satellite_risk,
            ),
        ),
        2,
    )

    # ========================================================
    # STATUS
    # ========================================================

    if satellite_risk < 25:
        status = "LOW"

    elif satellite_risk < 50:
        status = "MODERATE"

    elif satellite_risk < 75:
        status = "HIGH"

    else:
        status = "CRITICAL"

    # ========================================================
    # RETURN SATELLITE DATA
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

        vegetation_risk=round(
            vegetation_risk,
            2,
        ),

        wetness_risk=round(
            wetness_risk,
            2,
        ),

        satellite_risk=satellite_risk,

        source="SATELLITE_INTELLIGENCE_PROTOTYPE",

        status=status,

    )