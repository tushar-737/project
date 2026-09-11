from pathlib import Path

import pandas as pd

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


FEATURES = [
    "elevation",
    "slope_angle",
]


TARGET = "label"


def main():

    print("=" * 70)
    print("NER LandslideAI - Spatial Validation")
    print("=" * 70)

    print("\nLoading dataset...")

    df = pd.read_csv(INPUT_PATH)

    print(f"Total samples: {len(df)}")

    # --------------------------------------------------
    # CREATE SPATIAL GRID
    # --------------------------------------------------

    # Divide NER geographically.
    # A 1-degree longitude grid is used as a simple
    # geographic holdout strategy.

    df["spatial_group"] = (
        df["longitude"].astype(int)
    )

    print("\nSpatial groups:")

    print(
        df["spatial_group"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    # --------------------------------------------------
    # HOLD OUT EASTERN REGION
    # --------------------------------------------------

    # Test on the eastern part of the NER.
    # Train on western/central locations.

    test_groups = [
        df["spatial_group"].max()
    ]

    print(
        f"\nTest spatial group: {test_groups}"
    )

    train_df = df[
        ~df["spatial_group"].isin(test_groups)
    ].copy()

    test_df = df[
        df["spatial_group"].isin(test_groups)
    ].copy()

    print(
        f"\nTraining samples: {len(train_df)}"
    )

    print(
        f"Testing samples: {len(test_df)}"
    )

    # --------------------------------------------------
    # PREPARE DATA
    # --------------------------------------------------

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET]

    X_test = test_df[FEATURES]
    y_test = test_df[TARGET]

    # --------------------------------------------------
    # TRAIN MODEL
    # --------------------------------------------------

    print("\nTraining model on spatially separate data...")

    model = RandomForestClassifier(

        n_estimators=200,

        max_depth=20,

        min_samples_split=5,

        min_samples_leaf=2,

        random_state=42,

        n_jobs=-1,

        class_weight="balanced",

    )

    model.fit(
        X_train,
        y_train,
    )

    # --------------------------------------------------
    # EVALUATE
    # --------------------------------------------------

    predictions = model.predict(X_test)

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    roc_auc = roc_auc_score(
        y_test,
        probabilities,
    )

    print("\n" + "=" * 70)
    print("SPATIAL VALIDATION RESULTS")
    print("=" * 70)

    print(
        f"\nAccuracy: {accuracy:.4f}"
    )

    print(
        f"ROC-AUC Score: {roc_auc:.4f}"
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

    print("\n" + "=" * 70)
    print("SPATIAL VALIDATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()