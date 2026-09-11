from pathlib import Path

import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)


BASE_DIR = Path(__file__).resolve().parent


INPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "landslide_ml_dataset.csv"
)


MODEL_DIR = (
    BASE_DIR
    / "models"
)


MODEL_PATH = (
    MODEL_DIR
    / "landslide_random_forest.joblib"
)


FEATURES = [
    "latitude",
    "longitude",
    "elevation",
    "slope_angle",
]


TARGET = "label"


def main():

    print("=" * 70)
    print("NER LandslideAI - Random Forest Model Training")
    print("=" * 70)


    # --------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------

    print("\nLoading ML dataset...")

    df = pd.read_csv(INPUT_PATH)

    print(f"Total samples: {len(df)}")

    print(f"Features: {FEATURES}")


    # --------------------------------------------------
    # PREPARE FEATURES
    # --------------------------------------------------

    X = df[FEATURES]

    y = df[TARGET]


    print("\nTarget distribution:")

    print(y.value_counts())


    # --------------------------------------------------
    # TRAIN / TEST SPLIT
    # --------------------------------------------------

    print("\nSplitting dataset...")

    X_train, X_test, y_train, y_test = train_test_split(

        X,
        y,

        test_size=0.20,

        random_state=42,

        stratify=y,

    )


    print(f"Training samples: {len(X_train)}")

    print(f"Testing samples: {len(X_test)}")


    # --------------------------------------------------
    # CREATE MODEL
    # --------------------------------------------------

    print("\nTraining Random Forest model...")

    model = RandomForestClassifier(

        n_estimators=200,

        max_depth=20,

        min_samples_split=5,

        min_samples_leaf=2,

        random_state=42,

        n_jobs=-1,

        class_weight="balanced",

    )


    # --------------------------------------------------
    # TRAIN
    # --------------------------------------------------

    model.fit(
        X_train,
        y_train,
    )


    print("Training complete!")


    # --------------------------------------------------
    # PREDICTION
    # --------------------------------------------------

    print("\nEvaluating model...")

    predictions = model.predict(X_test)

    probabilities = model.predict_proba(
        X_test
    )[:, 1]


    # --------------------------------------------------
    # METRICS
    # --------------------------------------------------

    accuracy = accuracy_score(

        y_test,
        predictions,

    )


    roc_auc = roc_auc_score(

        y_test,
        probabilities,

    )


    print("\n" + "=" * 70)

    print("MODEL RESULTS")

    print("=" * 70)


    print(
        f"\nAccuracy: "
        f"{accuracy:.4f}"
    )


    print(
        f"ROC-AUC Score: "
        f"{roc_auc:.4f}"
    )


    print("\nConfusion Matrix:")

    print(

        confusion_matrix(
            y_test,
            predictions,
        )

    )


    print("\nClassification Report:")

    print(

        classification_report(
            y_test,
            predictions,
        )

    )


    # --------------------------------------------------
    # FEATURE IMPORTANCE
    # --------------------------------------------------

    print("\nFeature Importance:")

    importance = pd.DataFrame({

        "feature": FEATURES,

        "importance": model.feature_importances_,

    })

    importance = importance.sort_values(

        by="importance",

        ascending=False,

    )


    print(

        importance.to_string(
            index=False
        )

    )


    # --------------------------------------------------
    # SAVE MODEL
    # --------------------------------------------------

    MODEL_DIR.mkdir(

        parents=True,

        exist_ok=True,

    )


    joblib.dump(

        {
            "model": model,

            "features": FEATURES,

        },

        MODEL_PATH,

    )


    print("\n" + "=" * 70)

    print("MODEL TRAINING COMPLETE")

    print("=" * 70)


    print("\nModel saved:")

    print(MODEL_PATH)


if __name__ == "__main__":

    main()