"""
Feature preparation utilities for the LandslideAI ML model.

This module converts environmental and location data into the
feature format required by the trained ML model.
"""

FEATURE_NAMES = [
    "rainfall",
    "soil_moisture",
    "slope_angle",
    "elevation",
    "humidity",
    "temperature",
    "historical_factor",
]


def build_features(
    rainfall=None,
    soil_moisture=None,
    slope_angle=None,
    elevation=None,
    humidity=None,
    temperature=None,
    historical_factor=None,
):
    """
    Build a single ML feature dictionary.

    Missing values are replaced with None here.
    The training/prediction pipeline will handle imputation.
    """

    return {
        "rainfall": rainfall,
        "soil_moisture": soil_moisture,
        "slope_angle": slope_angle,
        "elevation": elevation,
        "humidity": humidity,
        "temperature": temperature,
        "historical_factor": historical_factor,
    }


def feature_vector(data):
    """
    Convert a feature dictionary into a list
    in the correct ML feature order.
    """

    return [
        data.get("rainfall"),
        data.get("soil_moisture"),
        data.get("slope_angle"),
        data.get("elevation"),
        data.get("humidity"),
        data.get("temperature"),
        data.get("historical_factor"),
    ]


def get_feature_names():
    """Return the ordered list of ML feature names."""

    return FEATURE_NAMES.copy()