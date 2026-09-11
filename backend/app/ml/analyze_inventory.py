from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "landslide_inventory_clean.csv"
)


def main():

    print("=" * 70)
    print("NER LandslideAI - Inventory Dataset Analysis")
    print("=" * 70)

    if not DATA_PATH.exists():
        print("\nERROR: Clean dataset not found!")
        print(DATA_PATH)
        return

    # Load dataset
    df = pd.read_csv(DATA_PATH)

    print("\nBASIC INFORMATION")
    print("-" * 70)

    print(f"Total records: {len(df)}")
    print(f"Total columns: {len(df.columns)}")

    print("\nCOLUMN NAMES:")
    print(list(df.columns))

    # --------------------------------------------------
    # UNIQUE STATES
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("RECORDS BY STATE")
    print("=" * 70)

    print(
        df["state"]
        .value_counts()
        .sort_values(ascending=False)
        .to_string()
    )

    # --------------------------------------------------
    # UNIQUE DISTRICTS
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("DISTRICT INFORMATION")
    print("=" * 70)

    print(
        f"Unique districts: "
        f"{df['district'].nunique()}"
    )

    # --------------------------------------------------
    # COORDINATE ANALYSIS
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("COORDINATE ANALYSIS")
    print("=" * 70)

    print(
        f"Latitude range: "
        f"{df['latitude'].min()} "
        f"to "
        f"{df['latitude'].max()}"
    )

    print(
        f"Longitude range: "
        f"{df['longitude'].min()} "
        f"to "
        f"{df['longitude'].max()}"
    )

    unique_coordinates = (
        df[
            ["latitude", "longitude"]
        ]
        .drop_duplicates()
        .shape[0]
    )

    print(
        f"Unique coordinate pairs: "
        f"{unique_coordinates}"
    )

    duplicate_coordinates = (
        len(df)
        - unique_coordinates
    )

    print(
        f"Duplicate coordinate records: "
        f"{duplicate_coordinates}"
    )

    # --------------------------------------------------
    # MOVEMENT TYPES
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("MOVEMENT TYPES")
    print("=" * 70)

    print(
        df["movement_type"]
        .value_counts(dropna=False)
        .head(20)
        .to_string()
    )

    # --------------------------------------------------
    # MATERIAL TYPES
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("MATERIAL INVOLVED")
    print("=" * 70)

    print(
        df["material"]
        .value_counts(dropna=False)
        .head(20)
        .to_string()
    )

    # --------------------------------------------------
    # MISSING VALUES
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("MISSING VALUES")
    print("=" * 70)

    print(
        df.isnull()
        .sum()
        .sort_values(ascending=False)
        .to_string()
    )

    # --------------------------------------------------
    # DUPLICATE SLIDE IDS
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("SLIDE ID ANALYSIS")
    print("=" * 70)

    print(
        f"Unique slide IDs: "
        f"{df['slide_id'].nunique()}"
    )

    duplicate_slide_ids = (
        df["slide_id"]
        .duplicated()
        .sum()
    )

    print(
        f"Duplicate slide IDs: "
        f"{duplicate_slide_ids}"
    )

    # --------------------------------------------------
    # SAMPLE DATA
    # --------------------------------------------------

    print("\n" + "=" * 70)
    print("RANDOM SAMPLE")
    print("=" * 70)

    print(
        df.sample(
            min(10, len(df)),
            random_state=42
        ).to_string(index=False)
    )

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()