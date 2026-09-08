"""Sensor data source abstraction.

The whole application reads environmental conditions through
`SensorDataSource`. Today only the simulated source exists because no
physical hardware (rain gauges, soil moisture probes, ESP32/Arduino nodes)
is attached; the architecture below is the exact seam where a real IoT
source plugs in later:

    SensorDataSource          (abstract interface)
    |-- SimulatedSensorService  (current prototype - used by the app)
    |-- RealIoTSensorService    (future - see class docstring for the
                                 integration sketch; requires hardware +
                                 a gateway endpoint that POSTs samples)

SWAPPING TO REAL SENSORS
------------------------
1. Build/deploy the gateway: ESP32/Arduino + sensors posts JSON to
   POST /api/environment/ingest {location_id, rainfall, soil_moisture,
   temperature, humidity, slope_angle}.
2. Implement RealIoTSensorService.read(location) which pulls the latest
   reading from the gateway/DB and return it as SensorSample.
3. Change the factory in `get_sensor_service()` to return it.

Everything else (risk pipeline, alerts, dashboard) keeps working untouched.
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

# --------------------------------------------------------------------------
# Simulation scenarios and their value ranges (realistic for the North
# Eastern Region monsoon).
# --------------------------------------------------------------------------
NORMAL = "NORMAL"
MODERATE_RAIN = "MODERATE_RAIN"
HEAVY_RAIN = "HEAVY_RAIN"
EXTREME_RAIN = "EXTREME_RAIN"
SCENARIOS = [NORMAL, MODERATE_RAIN, HEAVY_RAIN, EXTREME_RAIN]

SCENARIO_RANGES: dict[str, dict] = {
    NORMAL: {
        "rainfall": (0, 20),
        "soil_moisture": (25, 55),
        "temperature": (16, 34),
        "humidity": (45, 80),
    },
    MODERATE_RAIN: {
        "rainfall": (20, 80),
        "soil_moisture": (50, 75),
        "temperature": (18, 32),
        "humidity": (65, 90),
    },
    HEAVY_RAIN: {
        "rainfall": (150, 300),
        "soil_moisture": (70, 100),
        "temperature": (17, 28),
        "humidity": (80, 100),
    },
    EXTREME_RAIN: {
        "rainfall": (250, 500),  # 24h cumulative cloudburst / monsoon surge
        "soil_moisture": (85, 100),
        "temperature": (15, 25),
        "humidity": (85, 100),
    },
}

SCENARIO_LABELS = {
    NORMAL: "Normal weather",
    MODERATE_RAIN: "Moderate rain",
    HEAVY_RAIN: "Heavy rain",
    EXTREME_RAIN: "Extreme rain",
}


@dataclass
class SensorSample:
    """Normalised sample produced by any sensor source."""

    rainfall: float       # mm / 24h
    soil_moisture: float  # %
    temperature: float    # deg C
    humidity: float       # %
    slope_angle: float    # deg
    scenario: str


class SensorDataSource(ABC):
    """Interface every sensor source must satisfy."""

    @abstractmethod
    def read(self, location) -> SensorSample:
        """Return one current sample for the given location row."""
        ...


class SimulatedSensorService(SensorDataSource):
    """Generates physically plausible simulated telemetry.

    Values are drawn inside the scenario ranges, tilted by the location's
    own characteristics (a steeper location shows marginally higher slope
    readings; wetter micro-climates sit at the top of the humidity band).
    Ranges can be overridden per call for deterministic tests.
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    def _within(self, lo: float, hi: float, tilt: float = 0.0) -> float:
        """Random value in [lo, hi], tilted toward the top when tilt > 0."""
        v = self._rng.uniform(lo, hi)
        if tilt > 0:
            v = v * (1 - tilt) + (lo + (hi - lo) * 0.85) * tilt
        return round(max(0.0, v), 1)

    def read(self, location, scenario: str = HEAVY_RAIN,
             ranges: Optional[dict] = None) -> SensorSample:
        scenario = scenario if scenario in SCENARIOS else HEAVY_RAIN
        r = ranges or SCENARIO_RANGES[scenario]

        r_lo, r_hi = r["rainfall"]
        s_lo, s_hi = r["soil_moisture"]
        t_lo, t_hi = r["temperature"]
        h_lo, h_hi = r["humidity"]

        tilt = min(0.6, max(0.0, (location.slope_angle - 15) / 60.0))
        return SensorSample(
            rainfall=self._within(r_lo, r_hi, 0.35 if scenario != NORMAL else 0.0),
            soil_moisture=self._within(s_lo, s_hi, tilt),
            temperature=round(self._rng.uniform(t_lo, t_hi), 1),
            humidity=self._within(h_lo, h_hi, tilt),
            slope_angle=round(self._rng.uniform(
                max(0.0, location.slope_angle - 1.5),
                min(90.0, location.slope_angle + 2.0)), 1),
            scenario=scenario,
        )

    def scenarios(self) -> List[str]:
        return list(SCENARIOS)


class RealIoTSensorService(SensorDataSource):
    """Future integration point for physical IoT hardware.

    Sketch (requires hardware, therefore NOT enabled in this prototype):

        import httpx
        class RealIoTSensorService(SensorDataSource):
            def __init__(self, gateway_url="http://iot-gateway.local"):
                self.gateway_url = gateway_url

            def read(self, location) -> SensorSample:
                payload = httpx.get(f"{self.gateway_url}/sensors/{location.id}",
                                    timeout=5).json()
                return SensorSample(**payload, scenario="REAL_IOT")

    The gateway (ESP32/Arduino with rain gauge + soil moisture + DHT22)
    POSTs readings to POST /api/environment/ingest; that endpoint feeds the
    exact same automatic pipeline used by the simulator.
    """

    def read(self, location) -> SensorSample:
        raise NotImplementedError("Real IoT integration requires hardware - see README.")


def get_sensor_service() -> SensorDataSource:
    """Factory used by the whole app - returns the simulator today."""
    return SimulatedSensorService()
