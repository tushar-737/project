"""
NER LandslideAI - Landslide Risk Prediction Engine.

Prototype ML-style risk scoring based on environmental factors.
"""

from typing import Dict


def predict_landslide_risk(
    rainfall: float,
    soil_moisture: float,
    slope_angle: float,
) -> Dict:
    """
    Calculate a landslide risk score.

    Parameters:
        rainfall: Rainfall in mm
        soil_moisture: Soil moisture percentage
        slope_angle: Terrain slope angle in degrees
    """

    # Rainfall contribution (0-40)
    rainfall_score = min(rainfall / 200 * 40, 40)

    # Soil moisture contribution (0-30)
    moisture_score = min(soil_moisture / 100 * 30, 30)

    # Slope contribution (0-30)
    slope_score = min(slope_angle / 60 * 30, 30)

    # Total risk score
    risk_score = rainfall_score + moisture_score + slope_score

    # Ensure score stays between 0 and 100
    risk_score = max(0, min(100, risk_score))

    # Determine risk level
    if risk_score < 25:
        risk_level = "LOW"
    elif risk_score < 50:
        risk_level = "MODERATE"
    elif risk_score < 75:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    # Confidence for prototype
    confidence = 0.75

    # Explain contributing factors
    factors = []

    if rainfall > 100:
        factors.append("Heavy rainfall")

    if soil_moisture > 70:
        factors.append("High soil moisture")

    if slope_angle > 30:
        factors.append("Steep terrain")

    return {
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "confidence": confidence,
        "contributing_factors": factors,
    }