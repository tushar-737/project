"""
NER LandslideAI - Hybrid Landslide Risk Engine

Combines:

1. Random Forest ML terrain susceptibility model
2. Rainfall risk
3. Soil moisture risk
4. Historical landslide factor
5. Optional environmental context

Output:
LOW / MODERATE / HIGH / CRITICAL
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd


# ==========================================================
# PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "landslide_susceptibility_model.joblib"
)


# ==========================================================
# INPUT FEATURES
# ==========================================================

@dataclass
class RiskFeatures:

    rainfall: float
    soil_moisture: float
    slope_angle: float
    elevation: float

    historical_factor: float = 0.2

    humidity: float = 0.0
    temperature: float = 0.0


# ==========================================================
# PREDICTION RESULT
# ==========================================================

@dataclass
class RiskResult:

    score: float
    level: str
    confidence: float

    factors: list[str]

    terrain_risk: float
    rainfall_risk: float
    soil_moisture_risk: float
    historical_risk: float

    def as_dict(self):

        return {

            "risk_score": self.score,

            "risk_level": self.level,

            "confidence": self.confidence,

            "contributing_factors": self.factors,

            "terrain_risk": self.terrain_risk,

            "rainfall_risk": self.rainfall_risk,

            "soil_moisture_risk": self.soil_moisture_risk,

            "historical_risk": self.historical_risk,

        }


# ==========================================================
# RISK ENGINE
# ==========================================================

class LandslideRiskEngine:

    def __init__(self):

        self.model = None
        self.features = None

        self._load_model()


    # ------------------------------------------------------
    # LOAD TRAINED ML MODEL
    # ------------------------------------------------------

    def _load_model(self):

        if not MODEL_PATH.exists():

            raise FileNotFoundError(
                f"ML model not found at:\n{MODEL_PATH}\n\n"
                "This file is git-ignored (it's a trained binary, not source).\n"
                "Generate it once with:\n"
                "    cd backend\n"
                "    python -m app.ml.train_susceptibility_model\n"
                "This reads backend/app/ml/data/processed/landslide_ml_dataset.csv "
                "and writes the .joblib file this engine loads."
            )


        model_data = joblib.load(MODEL_PATH)


        self.model = model_data["model"]

        self.features = model_data["features"]


        print(

            "Landslide susceptibility model loaded"

        )


    # ------------------------------------------------------
    # TERRAIN RISK
    # ------------------------------------------------------

    def calculate_terrain_risk(

        self,

        elevation: float,

        slope_angle: float,

    ) -> float:


        feature_data = pd.DataFrame(

            [[

                elevation,

                slope_angle,

            ]],

            columns=self.features,

        )


        probability = (

            self.model
            .predict_proba(feature_data)[0][1]

        )


        return round(

            probability * 100,

            2,

        )


    # ------------------------------------------------------
    # RAINFALL RISK
    # ------------------------------------------------------

    def calculate_rainfall_risk(

        self,

        rainfall: float,

    ) -> float:


        rainfall = max(

            0,

            rainfall,

        )


        if rainfall < 10:

            return 10


        elif rainfall < 30:

            return 25


        elif rainfall < 60:

            return 50


        elif rainfall < 100:

            return 75


        return 100


    # ------------------------------------------------------
    # SOIL MOISTURE RISK
    # ------------------------------------------------------

    def calculate_soil_moisture_risk(

        self,

        soil_moisture: float,

    ) -> float:


        soil_moisture = max(

            0,

            min(

                100,

                soil_moisture,

            ),

        )


        if soil_moisture < 20:

            return 10


        elif soil_moisture < 40:

            return 30


        elif soil_moisture < 60:

            return 60


        elif soil_moisture < 80:

            return 80


        return 100


    # ------------------------------------------------------
    # HISTORICAL RISK
    # ------------------------------------------------------

    def calculate_historical_risk(

        self,

        historical_factor: float,

    ) -> float:


        historical_factor = max(

            0.0,

            min(

                1.0,

                historical_factor,

            ),

        )


        return round(

            historical_factor * 100,

            2,

        )


    # ------------------------------------------------------
    # FINAL SCORE
    # ------------------------------------------------------

    def calculate_final_score(

        self,

        terrain_risk: float,

        rainfall_risk: float,

        soil_risk: float,

        historical_risk: float,

    ) -> float:


        score = (

            terrain_risk * 0.35

            +

            rainfall_risk * 0.30

            +

            soil_risk * 0.20

            +

            historical_risk * 0.15

        )


        return round(

            max(

                0,

                min(

                    100,

                    score,

                ),

            ),

            2,

        )


    # ------------------------------------------------------
    # RISK LEVEL
    # ------------------------------------------------------

    def get_risk_level(

        self,

        score: float,

    ) -> str:


        if score < 25:

            return "LOW"


        elif score < 50:

            return "MODERATE"


        elif score < 75:

            return "HIGH"


        return "CRITICAL"


    # ------------------------------------------------------
    # CONTRIBUTING FACTORS
    # ------------------------------------------------------

    def get_contributing_factors(

        self,

        features: RiskFeatures,

        terrain_risk: float,

        rainfall_risk: float,

        soil_risk: float,

        historical_risk: float,

    ) -> list[str]:


        factors = []


        if rainfall_risk >= 75:

            factors.append(

                "High rainfall"

            )


        if soil_risk >= 80:

            factors.append(

                "Very high soil moisture"

            )


        if features.slope_angle >= 30:

            factors.append(

                "Steep terrain"

            )


        if terrain_risk >= 70:

            factors.append(

                "High terrain susceptibility"

            )


        if historical_risk >= 70:

            factors.append(

                "Historical landslide-prone area"

            )


        if not factors:

            factors.append(

                "Environmental conditions within normal range"

            )


        return factors


    # ------------------------------------------------------
    # COMPLETE PREDICTION
    # ------------------------------------------------------

    def predict(

        self,

        features: RiskFeatures,

        location=None,

    ) -> RiskResult:


        terrain_risk = (

            self.calculate_terrain_risk(

                features.elevation,

                features.slope_angle,

            )

        )


        rainfall_risk = (

            self.calculate_rainfall_risk(

                features.rainfall,

            )

        )


        soil_risk = (

            self.calculate_soil_moisture_risk(

                features.soil_moisture,

            )

        )


        historical_risk = (

            self.calculate_historical_risk(

                features.historical_factor,

            )

        )


        score = (

            self.calculate_final_score(

                terrain_risk,

                rainfall_risk,

                soil_risk,

                historical_risk,

            )

        )


        level = (

            self.get_risk_level(

                score,

            )

        )


        factors = (

            self.get_contributing_factors(

                features,

                terrain_risk,

                rainfall_risk,

                soil_risk,

                historical_risk,

            )

        )


        return RiskResult(

            score=score,

            level=level,

            confidence=0.75,

            factors=factors,

            terrain_risk=terrain_risk,

            rainfall_risk=rainfall_risk,

            soil_moisture_risk=soil_risk,

            historical_risk=historical_risk,

        )


# ==========================================================
# SINGLETON ENGINE
# ==========================================================

_ENGINE = None


def get_risk_engine() -> LandslideRiskEngine:


    global _ENGINE


    if _ENGINE is None:

        _ENGINE = LandslideRiskEngine()


    return _ENGINE