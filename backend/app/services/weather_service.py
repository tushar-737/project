from dataclasses import dataclass
from datetime import datetime, timedelta

import requests


# ============================================================
# OPEN-METEO CONFIGURATION
# ============================================================

BASE_URL = "https://api.open-meteo.com/v1/forecast"

# (connect timeout, read timeout)
REQUEST_TIMEOUT = (5, 10)


# ============================================================
# WEATHER SAMPLE
# ============================================================

@dataclass
class WeatherSample:
    # Rainfall accumulated during the previous 24 hours.
    rainfall: float

    # Antecedent rainfall accumulated before the current time.
    rainfall_72h: float
    rainfall_7d: float

    # Current environmental conditions.
    soil_moisture: float
    temperature: float
    humidity: float

    # Terrain information.
    slope_angle: float

    # Scenario derived from recent rainfall.
    scenario: str

    # Data source information.
    source: str = "OPEN_METEO"


# ============================================================
# DETERMINE RAINFALL SCENARIO
# ============================================================

def determine_scenario(rainfall: float) -> str:
    """
    Convert 24-hour accumulated rainfall
    into project scenario levels.
    """

    if rainfall >= 150:
        return "EXTREME_RAIN"

    if rainfall >= 75:
        return "HEAVY_RAIN"

    if rainfall >= 25:
        return "MODERATE_RAIN"

    return "NORMAL"


# ============================================================
# FETCH LIVE WEATHER FROM OPEN-METEO
# ============================================================

def get_live_weather(
    latitude: float,
    longitude: float,
) -> dict:
    """
    Fetch real weather and soil moisture data
    from Open-Meteo.
    """

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

        # Previous data required for antecedent
        # rainfall calculations.
        "past_days": 7,

        # Forecast data for 24h and 48h prediction.
        "forecast_days": 3,

        "timezone": "auto",
    }

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Open-Meteo request failed: {str(exc)}"
        )


# ============================================================
# CONVERT LIVE WEATHER TO AI PIPELINE SAMPLE
# ============================================================

def get_weather_sample(location) -> WeatherSample:
    """
    Fetch real environmental data and convert it
    into a format compatible with the AI risk pipeline.
    """

    data = get_live_weather(
        location.latitude,
        location.longitude,
    )


    # ========================================================
    # CURRENT WEATHER
    # ========================================================

    current = data.get("current")

    if not current:
        raise ValueError(
            "Current weather data unavailable"
        )

    temperature = current.get(
        "temperature_2m"
    )

    humidity = current.get(
        "relative_humidity_2m"
    )

    if temperature is None:
        raise ValueError(
            "Temperature data unavailable"
        )

    if humidity is None:
        raise ValueError(
            "Humidity data unavailable"
        )

    current_time_string = current.get("time")

    if not current_time_string:
        raise ValueError(
            "Current weather timestamp unavailable"
        )

    current_time = datetime.fromisoformat(
        current_time_string
    )


    # ========================================================
    # HOURLY WEATHER DATA
    # ========================================================

    hourly = data.get("hourly")

    if not hourly:
        raise ValueError(
            "Hourly weather data unavailable"
        )

    hourly_times = hourly.get("time")

    precipitation_values = hourly.get(
        "precipitation"
    )

    soil_moisture_values = hourly.get(
        "soil_moisture_3_to_9cm"
    )

    if (
        not hourly_times
        or precipitation_values is None
        or soil_moisture_values is None
    ):
        raise ValueError(
            "Required hourly weather data unavailable"
        )


    # ========================================================
    # CALCULATE ANTECEDENT RAINFALL
    # ========================================================

    # Landslides are influenced not only by
    # immediate rainfall but also by accumulated
    # rainfall over previous days.

    start_24h = (
        current_time
        - timedelta(hours=24)
    )

    start_72h = (
        current_time
        - timedelta(hours=72)
    )

    start_7d = (
        current_time
        - timedelta(days=7)
    )

    rainfall_24h = 0.0
    rainfall_72h = 0.0
    rainfall_7d = 0.0


    for time_string, rainfall_value in zip(
        hourly_times,
        precipitation_values,
    ):

        if rainfall_value is None:
            continue

        sample_time = datetime.fromisoformat(
            time_string
        )

        rainfall_value = float(
            rainfall_value
        )

        # Do not include future forecast data.
        if sample_time > current_time:
            continue


        # Previous 24 hours.
        if (
            start_24h
            < sample_time
            <= current_time
        ):
            rainfall_24h += rainfall_value


        # Previous 72 hours.
        if (
            start_72h
            < sample_time
            <= current_time
        ):
            rainfall_72h += rainfall_value


        # Previous 7 days.
        if (
            start_7d
            < sample_time
            <= current_time
        ):
            rainfall_7d += rainfall_value


    # ========================================================
    # GET LATEST REAL SOIL MOISTURE
    # ========================================================

    latest_soil_moisture = None


    for time_string, moisture_value in zip(
        reversed(hourly_times),
        reversed(soil_moisture_values),
    ):

        if moisture_value is None:
            continue


        sample_time = datetime.fromisoformat(
            time_string
        )


        # Do not use future forecast data.
        if sample_time <= current_time:

            latest_soil_moisture = float(
                moisture_value
            )

            break


    if latest_soil_moisture is None:
        raise ValueError(
            "Real soil moisture data unavailable"
        )


    # ========================================================
    # CONVERT SOIL MOISTURE TO PERCENTAGE
    # ========================================================

    # Open-Meteo provides volumetric water content
    # in m³/m³.

    soil_moisture_percent = (
        latest_soil_moisture * 100
    )


    # Prevent unexpected values.
    soil_moisture_percent = max(
        0.0,
        min(
            soil_moisture_percent,
            100.0,
        ),
    )


    # ========================================================
    # DETERMINE SCENARIO
    # ========================================================

    scenario = determine_scenario(
        rainfall_24h
    )


    # ========================================================
    # RETURN AI PIPELINE SAMPLE
    # ========================================================

    return WeatherSample(

        # Previous 24-hour rainfall.
        rainfall=round(
            rainfall_24h,
            2,
        ),

        # Antecedent rainfall.
        rainfall_72h=round(
            rainfall_72h,
            2,
        ),

        rainfall_7d=round(
            rainfall_7d,
            2,
        ),

        # Environmental data.
        soil_moisture=round(
            soil_moisture_percent,
            2,
        ),

        temperature=round(
            float(temperature),
            2,
        ),

        humidity=round(
            float(humidity),
            2,
        ),

        # Terrain data.
        slope_angle=float(
            location.slope_angle
        ),

        scenario=scenario,

        source="OPEN_METEO",
    )


# ============================================================
# FORECAST RAINFALL
# ============================================================

def get_forecast_rainfall(location) -> dict:
    """
    Calculate forecast rainfall for the
    next 24 and 48 hours.
    """

    data = get_live_weather(
        location.latitude,
        location.longitude,
    )


    # ========================================================
    # GET WEATHER DATA
    # ========================================================

    current = data.get("current")
    hourly = data.get("hourly")


    if not current:
        raise ValueError(
            "Current weather data unavailable"
        )


    if not hourly:
        raise ValueError(
            "Hourly weather data unavailable"
        )


    current_time_string = current.get("time")


    if not current_time_string:
        raise ValueError(
            "Current weather timestamp unavailable"
        )


    current_time = datetime.fromisoformat(
        current_time_string
    )


    hourly_times = hourly.get("time")

    precipitation_values = hourly.get(
        "precipitation"
    )


    if (
        not hourly_times
        or precipitation_values is None
    ):
        raise ValueError(
            "Forecast rainfall data unavailable"
        )


    # ========================================================
    # FORECAST TIME WINDOWS
    # ========================================================

    next_24h = (
        current_time
        + timedelta(hours=24)
    )


    next_48h = (
        current_time
        + timedelta(hours=48)
    )


    rainfall_next_24h = 0.0
    rainfall_next_48h = 0.0


    # ========================================================
    # CALCULATE FORECAST RAINFALL
    # ========================================================

    for time_string, rainfall_value in zip(
        hourly_times,
        precipitation_values,
    ):

        if rainfall_value is None:
            continue


        sample_time = datetime.fromisoformat(
            time_string
        )


        rainfall_value = float(
            rainfall_value
        )


        # Next 24 hours.
        if (
            current_time
            < sample_time
            <= next_24h
        ):
            rainfall_next_24h += (
                rainfall_value
            )


        # Next 48 hours.
        if (
            current_time
            < sample_time
            <= next_48h
        ):
            rainfall_next_48h += (
                rainfall_value
            )


    # ========================================================
    # RETURN FORECAST
    # ========================================================

    return {

        "next_24h": round(
            rainfall_next_24h,
            2,
        ),

        "next_48h": round(
            rainfall_next_48h,
            2,
        ),

    }