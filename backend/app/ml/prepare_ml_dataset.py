from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent


INPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "landslide_training_with_terrain.csv"
)


OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "landslide_ml_dataset.csv"
)


def main():

    print("=" * 70)
    print("NER LandslideAI - ML Dataset Preparation")
    print("=" * 70)


    print("\nLoading terrain dataset...")

    df = pd.read_csv(INPUT_PATH)

    print(f"Total samples: {len(df)}")


    print("\nChecking missing values...")

    print(
        df[
            [
                "latitude",
                "longitude",
                "elevation",
                "slope_angle",
                "label",
            ]
        ]
        .isna()
        .sum()
    )


    print("\nRemoving samples with missing terrain data...")

    df = df.dropna(
        subset=[
            "elevation",
            "slope_angle",
        ]
    )


    print(
        f"Samples remaining: {len(df)}"
    )


    print("\nSelecting ML features...")


    ml_df = df[
        [
            "latitude",
            "longitude",
            "elevation",
            "slope_angle",
            "label",
        ]
    ].copy()


    print("\nFinal dataset columns:")

    print(
        ml_df.columns.tolist()
    )


    print("\nLabel distribution:")

    print(
        ml_df["label"]
        .value_counts()
    )


    ml_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )


    print("\n" + "=" * 70)
    print("ML DATASET PREPARATION COMPLETE")
    print("=" * 70)


    print(
        f"\nFinal samples: {len(ml_df)}"
    )


    print(
        "\nSaved dataset:"
    )

    print(
        OUTPUT_PATH
    )


if __name__ == "__main__":
    main()