"""
NER LandslideAI - ML Model Training.

This script trains multiple machine-learning models using a CSV dataset
and saves the best-performing model.

Expected dataset columns:

rainfall
soil_moisture
slope_angle
elevation
humidity
temperature
historical_factor
landslide_occurred
"""

from pathlib import Path
import sys

import joblib
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

from .features import FEATURE_NAMES


BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "data" / "processed" / "landslide_training_data.csv"

MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "landslide_model.joblib"


def load_dataset():
    """Load and validate the training dataset."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"\nTraining dataset not found:\n{DATA_PATH}\n\n"
            "Add your dataset as:\n"
            "backend/app/ml/data/processed/landslide_training_data.csv"
        )

    df = pd.read_csv(DATA_PATH)

    required_columns = FEATURE_NAMES + ["landslide_occurred"]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Dataset is missing required columns: {missing}"
        )

    return df


def evaluate_model(name, model, X_test, y_test):
    """Evaluate one trained model."""

    predictions = model.predict(X_test)

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(X_test)[:, 1]
    else:
        probabilities = predictions

    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(
            y_test,
            predictions,
            zero_division=0
        ),
        "recall": recall_score(
            y_test,
            predictions,
            zero_division=0
        ),
        "f1": f1_score(
            y_test,
            predictions,
            zero_division=0
        ),
    }

    # ROC-AUC requires both classes in the test set.
    if len(set(y_test)) > 1:
        metrics["roc_auc"] = roc_auc_score(
            y_test,
            probabilities
        )
    else:
        metrics["roc_auc"] = 0.0

    print(f"\n{name}")
    print("-" * 40)

    for metric, value in metrics.items():
        print(f"{metric:12}: {value:.4f}")

    return metrics


def train():
    """Train and select the best landslide prediction model."""

    print("\nNER LandslideAI - Model Training")
    print("=" * 45)

    df = load_dataset()

    print(f"\nDataset loaded successfully")
    print(f"Total samples: {len(df)}")

    X = df[FEATURE_NAMES]
    y = df["landslide_occurred"]

    print(f"Landslide samples: {(y == 1).sum()}")
    print(f"Non-landslide samples: {(y == 0).sum()}")

    if y.nunique() < 2:
        raise ValueError(
            "Training data must contain both "
            "0 (no landslide) and 1 (landslide)."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    models = {
        "Logistic Regression": LogisticRegression(
            max_iter=2000
        ),

        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            random_state=42,
            class_weight="balanced"
        ),

        "Gradient Boosting": GradientBoostingClassifier(
            random_state=42
        ),
    }

    results = {}

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    best_model = None
    best_model_name = None
    best_score = -1

    for name, classifier in models.items():

        pipeline = Pipeline([
            (
                "imputer",
                SimpleImputer(strategy="median")
            ),
            (
                "model",
                classifier
            ),
        ])

        print(f"\nTraining {name}...")

        pipeline.fit(
            X_train,
            y_train
        )

        metrics = evaluate_model(
            name,
            pipeline,
            X_test,
            y_test
        )

        results[name] = metrics

        # F1 score is used for model selection.
        # Recall will also be examined because
        # missing a dangerous event is costly.
        if metrics["f1"] > best_score:

            best_score = metrics["f1"]

            best_model = pipeline

            best_model_name = name

    joblib.dump(
        {
            "model": best_model,
            "feature_names": FEATURE_NAMES,
            "model_name": best_model_name,
            "metrics": results[best_model_name],
        },
        MODEL_PATH
    )

    print("\n" + "=" * 45)

    print("BEST MODEL SELECTED")

    print(f"Model: {best_model_name}")
    print(f"F1 Score: {best_score:.4f}")

    print(f"\nSaved to:")
    print(MODEL_PATH)

    print("\nAll Results:")

    for name, metrics in results.items():
        print(
            f"\n{name}: "
            f"F1={metrics['f1']:.4f}, "
            f"Recall={metrics['recall']:.4f}, "
            f"ROC-AUC={metrics['roc_auc']:.4f}"
        )


if __name__ == "__main__":
    try:
        train()

    except Exception as error:

        print("\nTRAINING FAILED")

        print(error)

        sys.exit(1)