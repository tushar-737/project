from dataclasses import dataclass
from datetime import datetime, timedelta

import requests


BASE_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class WeatherSample:
    rainfall: float
    soil_moisture: float
    temperature: float
    humidity: float
    slope_angle: float
    scenario: str


def determine_scenario(rainfall: float) -> str:
    """Convert 24-hour accumulated rainfall into project scenario levels."""

    if rainfall >= 150:
        return "EXTREME_RAIN"

    if rainfall >= 75:
        return "HEAVY_RAIN"

    if rainfall >= 25:
        return "MODERATE_RAIN"

    return "NORMAL"


def get_live_weather(latitude: float, longitude: float) -> dict:
    """Fetch real weather and soil moisture data."""

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": (
            "temperature_2m,"
            "relative_humidity_2m"
        ),

        "hourly": (
            "precipitation,"
            "soil_moisture_3_to_9cm"
        ),

        # We need previous data to calculate
        # actual rainfall during the last 24 hours.
        "past_days": 2,
        "forecast_days": 3,

        "timezone": "auto",
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


def get_weather_sample(location) -> WeatherSample:
    """
    Fetch real environmental data and convert it
    into a format compatible with the risk pipeline.
    """

    data = get_live_weather(
        location.latitude,
        location.longitude,
    )

    current = data["current"]

    temperature = current["temperature_2m"]
    humidity = current["relative_humidity_2m"]

    # Current time returned by Open-Meteo.
    current_time = datetime.fromisoformat(
        current["time"]
    )

    # Start of the previous 24-hour window.
    start_time = current_time - timedelta(hours=24)

    hourly = data["hourly"]

    hourly_times = hourly["time"]
    precipitation_values = hourly["precipitation"]
    soil_moisture_values = hourly[
        "soil_moisture_3_to_9cm"
    ]

    # -------------------------------------------------
    # ACTUAL PREVIOUS 24-HOUR RAINFALL
    # -------------------------------------------------

    rainfall_24h = 0.0

    for time_string, rainfall_value in zip(
        hourly_times,
        precipitation_values,
    ):

        sample_time = datetime.fromisoformat(
            time_string
        )

        # Only include readings from:
        #
        # NOW - 24 HOURS
        #        ↓
        # NOW
        #
        if (
            start_time < sample_time <= current_time
            and rainfall_value is not None
        ):
            rainfall_24h += rainfall_value

    # -------------------------------------------------
    # LATEST AVAILABLE REAL SOIL MOISTURE
    # -------------------------------------------------

    latest_soil_moisture = None

    for time_string, moisture_value in zip(
        reversed(hourly_times),
        reversed(soil_moisture_values),
    ):

        sample_time = datetime.fromisoformat(
            time_string
        )

        # Do not accidentally use future forecast data.
        if (
            sample_time <= current_time
            and moisture_value is not None
        ):
            latest_soil_moisture = moisture_value
            break

    if latest_soil_moisture is None:
        raise ValueError(
            "Real soil moisture data is unavailable"
        )

    # Open-Meteo soil moisture is volumetric water
    # content in m³/m³. Convert it to percentage.
    soil_moisture_percent = (
        latest_soil_moisture * 100
    )

    scenario = determine_scenario(
        rainfall_24h
    )

    return WeatherSample(
        rainfall=round(rainfall_24h, 2),
        soil_moisture=round(
            soil_moisture_percent,
            2,
        ),
        temperature=round(temperature, 2),
        humidity=round(humidity, 2),
        slope_angle=location.slope_angle,
        scenario=scenario,
    )
def get_forecast_rainfall(location) -> dict:
    """
    Calculate forecast rainfall for the next
    24 and 48 hours.
    """

    data = get_live_weather(
        location.latitude,
        location.longitude,
    )

    current_time = datetime.fromisoformat(
        data["current"]["time"]
    )

    hourly_times = data["hourly"]["time"]
    precipitation_values = data["hourly"]["precipitation"]

    rainfall_next_24h = 0.0
    rainfall_next_48h = 0.0

    next_24h = current_time + timedelta(hours=24)
    next_48h = current_time + timedelta(hours=48)

    for time_string, rainfall_value in zip(
        hourly_times,
        precipitation_values,
    ):
        sample_time = datetime.fromisoformat(time_string)

        if rainfall_value is None:
            continue

        # Rainfall during the next 24 hours
        if current_time < sample_time <= next_24h:
            rainfall_next_24h += rainfall_value

        # Rainfall during the next 48 hours
        if current_time < sample_time <= next_48h:
            rainfall_next_48h += rainfall_value

    return {
        "next_24h": round(rainfall_next_24h, 2),
        "next_48h": round(rainfall_next_48h, 2),
    }