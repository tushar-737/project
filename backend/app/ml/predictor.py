"""
NER LandslideAI - Trained ML Model Predictor.

Loads the trained model and converts its prediction into
the format used by the rest of the application.
"""

from pathlib import Path

import joblib
import pandas as pd

from .features import FEATURE_NAMES, build_features


BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "landslide_model.joblib"


class LandslidePredictor:
    """Loads and uses the trained landslide ML model."""

    def __init__(self):
        self.bundle = None
        self.model = None

    def load_model(self):
        """Load the trained model from disk."""

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Trained ML model not found: {MODEL_PATH}. "
                "Train the model first."
            )

        self.bundle = joblib.load(MODEL_PATH)

        self.model = self.bundle["model"]

        return self.model

    def is_loaded(self):
        """Check whether the model is loaded."""

        return self.model is not None

    def predict(
        self,
        rainfall=None,
        soil_moisture=None,
        slope_angle=None,
        elevation=None,
        humidity=None,
        temperature=None,
        historical_factor=None,
    ):
        """
        Predict landslide probability.

        Returns:
            risk_score: 0 to 100
            probability: 0 to 1
            prediction: 0 or 1
        """

        if not self.is_loaded():
            self.load_model()

        features = build_features(
            rainfall=rainfall,
            soil_moisture=soil_moisture,
            slope_angle=slope_angle,
            elevation=elevation,
            humidity=humidity,
            temperature=temperature,
            historical_factor=historical_factor,
        )

        # Create DataFrame with the exact feature order
        # used during model training.
        X = pd.DataFrame(
            [[features[name] for name in FEATURE_NAMES]],
            columns=FEATURE_NAMES,
        )

        prediction = int(self.model.predict(X)[0])

        probability = float(
            self.model.predict_proba(X)[0][1]
        )

        risk_score = round(probability * 100, 2)

        return {
            "prediction": prediction,
            "probability": round(probability, 4),
            "risk_score": risk_score,
        }

    def model_info(self):
        """Return information about the loaded model."""

        if not self.is_loaded():
            self.load_model()

        return {
            "model_name": self.bundle.get(
                "model_name"
            ),
            "feature_names": self.bundle.get(
                "feature_names"
            ),
            "metrics": self.bundle.get(
                "metrics"
            ),
        }


# Shared predictor instance
predictor = LandslidePredictor()