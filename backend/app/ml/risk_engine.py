"""AI landslide risk engine.

Design
------
The engine is deliberately split into a stable interface (`BaseRiskEngine`)
and one implementation (`RuleBasedRiskEngine`). The pipeline code only talks
to the interface, so the prototype works today with a transparent,
explainable hybrid rule engine and can be swapped for a trained scikit-learn
model later WITHOUT touching any other module:

    ---------------------------------------------------------------------
    ML INTEGRATION POINT (future)
    ---------------------------------------------------------------------
    1. Train a classifier/regressor (e.g. GradientBoosting or RandomForest)
       on historical rainfall / soil moisture / slope / elevation / humidity
       samples labelled with observed landslide outcomes (sklearn is listed
       in requirements.txt for exactly this step).

    2. Add a `LearnedRiskEngine(BaseRiskEngine)` class below that wraps the
       pickled pipeline, e.g.:

           class LearnedRiskEngine(BaseRiskEngine):
               def __init__(self, model_path="models/landslide_rf.pkl"):
                   import joblib
                   self.model = joblib.load(model_path)
               def predict(self, features: RiskFeatures, location) -> RiskResult:
                   x = [[features.rainfall, features.soil_moisture, ...]]
                   proba = self.model.predict_proba(x)[0][1]   # P(landslide)
                   score = round(proba * 100, 1)
                   ...
                   return RiskResult(...)

       Tree models accept NaN naturally, so unmonitored locations degrade
       gracefully (proba -> prior), matching the rule engine behaviour.

    3. Choose the implementation in `get_risk_engine()`:

           return LearnedRiskEngine("ml/models/landslide_rf.pkl")

    No other file needs to change: services/pipeline.py, the REST APIs and
    the frontend all consume BaseRiskEngine outputs (score 0-100, level,
    confidence, contributing_factors).
    ---------------------------------------------------------------------

Input normalisation
-------------------
Each input is converted to a normalised score in [0, 100] via monotonic
piecewise-linear functions chosen from physical reasoning about landslide
triggers in the North Eastern Region (heavy monsoon rainfall, saturated
soil, steep slopes, humidity):
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

RISK_LEVELS = {"LOW", "MODERATE", "HIGH", "CRITICAL"}


# --------------------------------------------------------------------------
# Risk vocabulary shared by services, APIs and the frontend.
# --------------------------------------------------------------------------
RISK_LOW = "LOW"
RISK_MODERATE = "MODERATE"
RISK_HIGH = "HIGH"
RISK_CRITICAL = "CRITICAL"


def risk_level_for_score(score: float) -> str:
    """Map a 0-100 risk score to LOW / MODERATE / HIGH / CRITICAL."""
    if score >= 76:
        return RISK_CRITICAL
    if score >= 51:
        return RISK_HIGH
    if score >= 26:
        return RISK_MODERATE
    return RISK_LOW


@dataclass
class RiskFeatures:
    """All inputs the engine may consume (raw, physical units)."""

    rainfall: Optional[float] = None        # mm / 24h
    soil_moisture: Optional[float] = None   # %
    slope_angle: Optional[float] = None     # degrees
    elevation: Optional[float] = None       # metres (amplifier only)
    historical_factor: Optional[float] = None  # 0-1 static susceptibility
    humidity: Optional[float] = None        # %
    temperature: Optional[float] = None     # deg C (context, unused in rules)


@dataclass
class RiskResult:
    score: float
    level: str
    confidence: float
    factors: List[str]

    def as_dict(self) -> dict:
        return {
            "risk_score": round(self.score, 1),
            "risk_level": self.level,
            "confidence": round(self.confidence, 3),
            "contributing_factors": self.factors,
        }


class BaseRiskEngine(ABC):
    """Interface every risk engine (rule-based or ML) must implement."""

    @abstractmethod
    def predict(self, features: RiskFeatures, location=None) -> RiskResult:
        ...


def _linear(x: float, x0: float, x1: float, y0: float, y1: float) -> float:
    """Clamped piecewise-linear map from [x0, x1] to [y0, y1]."""
    if x <= x0:
        return y0
    if x >= x1:
        return y1
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)


class RuleBasedRiskEngine(BaseRiskEngine):
    """Hybrid weighted rule engine (default engine of the prototype).

    Sub-scores and weights (rainfall 30%, soil moisture 25%, slope 20%,
    historical susceptibility 15%, humidity 10%) are applied, then a small
    elevation + humidity amplifier nudges the total. The result is the
    weighted combination of evidence, each factor reported transparently so
    the alert message can name the actual contributors.

    IMPORTANT: this predicts RISK / PROBABILITY of a landslide over the
    current 24h window. It does NOT predict the exact time of an event.
    """

    WEIGHTS = {
        "rainfall": 0.30,
        "soil_moisture": 0.25,
        "slope": 0.20,
        "historical": 0.15,
        "humidity": 0.10,
    }

    def rainfall_score(self, mm: Optional[float]) -> tuple[float, Optional[str]]:
        if mm is None:
            return 20.0, None
        # <10mm calm monsoon day ... 300mm+ cloudburst
        s = _linear(mm, 0, 300, 0, 100)
        if mm >= 250:
            return s, "Extreme rainfall"
        if mm >= 100:
            return s, "Heavy rainfall"
        if mm >= 40:
            return s, "Moderate rainfall"
        return s, None

    def soil_score(self, sm: Optional[float]) -> tuple[float, Optional[str]]:
        if sm is None:
            return 15.0, None
        s = _linear(sm, 10, 100, 0, 100)
        if sm >= 85:
            return s, "Saturated soil"
        if sm >= 65:
            return s, "High soil moisture"
        if sm >= 45:
            return s, "Elevated soil moisture"
        return s, None

    def slope_score(self, deg: Optional[float]) -> tuple[float, Optional[str]]:
        if deg is None:
            return 15.0, None
        s = _linear(deg, 5, 60, 0, 100)
        if deg >= 40:
            return s, "Very steep slope"
        if deg >= 30:
            return s, "Steep slope"
        return s, None

    def humidity_score(self, h: Optional[float]) -> tuple[float, Optional[str]]:
        if h is None:
            return 15.0, None
        s = _linear(h, 30, 100, 0, 100)
        if h >= 80:
            return s, "High humidity"
        return s, None

    def predict(self, features: RiskFeatures, location=None) -> RiskResult:
        rainfall_s, rainfall_f = self.rainfall_score(features.rainfall)
        soil_s, soil_f = self.soil_score(features.soil_moisture)
        slope_s, slope_f = self.slope_score(features.slope_angle)
        humidity_s, humidity_f = self.humidity_score(features.humidity)

        historical_s = 100.0 * (features.historical_factor if features.historical_factor is not None else 0.2)
        hist_f = "Historical landslide-prone zone" if historical_s >= 60 else None

        raw = (
            rainfall_s * self.WEIGHTS["rainfall"]
            + soil_s * self.WEIGHTS["soil_moisture"]
            + slope_s * self.WEIGHTS["slope"]
            + historical_s * self.WEIGHTS["historical"]
            + humidity_s * self.WEIGHTS["humidity"]
        )

        # Elevation amplifier: NE India landslides cluster on 900-2000 m
        # hillslopes; peaks on 700-1800 m then tapers (valleys / very high
        # barren ridges are less landslide-prone).
        elevation = features.elevation or 0
        elev_amp = math.exp(-0.5 * ((elevation - 1200) / 900) ** 2) * 0.10
        score = min(100.0, raw * (1.0 + elev_amp) + 2.0 * (humidity_s / 100.0))

        level = risk_level_for_score(score)

        factors: List[str] = []
        for f in (rainfall_f, soil_f, slope_f, hist_f, humidity_f):
            if f and f not in factors:
                factors.append(f)

        # Confidence grows with the amount of live sensor evidence present.
        present = sum(1 for v in [features.rainfall, features.soil_moisture,
                                  features.slope_angle, features.humidity] if v is not None)
        confidence = round(0.45 + 0.12 * present, 3)

        return RiskResult(score=round(min(100.0, score), 1), level=level,
                          confidence=confidence, factors=factors)


def get_risk_engine() -> BaseRiskEngine:
    """Factory used by the whole app - swap the implementation here."""
    return RuleBasedRiskEngine()
