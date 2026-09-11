from pathlib import Path
import re

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent

INPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "landslide_inventory_clean.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "landslide_inventory_standardized.csv"
)


def normalize_text(value):

    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    value = re.sub(
        r"[-_/]+",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value


def normalize_movement(value):

    value = normalize_text(value)

    if value is None:
        return None

    if "SLIDE" in value:
        return "SLIDE"

    if "FALL" in value:
        return "FALL"

    if "FLOW" in value:
        return "FLOW"

    if "TOPPLE" in value:
        return "TOPPLE"

    if "CREEP" in value:
        return "CREEP"

    if "SUBSIDENCE" in value:
        return "SUBSIDENCE"

    if "COMPLEX" in value:
        return "COMPLEX"

    if "COMPOSITE" in value:
        return "COMPLEX"

    if value in ["NIL", "NA", "NONE"]:
        return None

    return value


def normalize_material(value):

    value = normalize_text(value)

    if value is None:
        return None

    if "ROCK" in value and "DEBRIS" in value:
        return "ROCK_CUM_DEBRIS"

    if "SOIL" in value and "DEBRIS" in value:
        return "SOIL_CUM_DEBRIS"

    if "EARTH" in value and "DEBRIS" in value:
        return "EARTH_CUM_DEBRIS"

    if "ROCK" in value:
        return "ROCK"

    if "DEBRIS" in value:
        return "DEBRIS"

    if "EARTH" in value:
        return "EARTH"

    if "SOIL" in value:
        return "SOIL"

    if "REGOLITH" in value:
        return "REGOLITH"

    if "COLLUVIUM" in value:
        return "COLLUVIUM"

    return value


def main():

    print("=" * 70)
    print("NER LandslideAI - Inventory Standardization")
    print("=" * 70)

    if not INPUT_PATH.exists():

        print("\nERROR: Input dataset not found!")
        print(INPUT_PATH)

        return

    print("\nLoading dataset...")

    df = pd.read_csv(INPUT_PATH)

    print(f"Records loaded: {len(df)}")

    # ------------------------------------------
    # ORIGINAL VALUES
    # ------------------------------------------

    print("\nORIGINAL MOVEMENT TYPES:")

    print(
        df["movement_type"]
        .value_counts(dropna=False)
        .head(20)
        .to_string()
    )

    # ------------------------------------------
    # STANDARDIZE MOVEMENT TYPE
    # ------------------------------------------

    print("\nStandardizing movement types...")

    df["movement_type"] = (
        df["movement_type"]
        .apply(normalize_movement)
    )

    # ------------------------------------------
    # STANDARDIZE MATERIAL
    # ------------------------------------------

    print("Standardizing material types...")

    df["material"] = (
        df["material"]
        .apply(normalize_material)
    )

    # ------------------------------------------
    # STANDARDIZE STATES
    # ------------------------------------------

    df["state"] = (
        df["state"]
        .astype(str)
        .str.strip()
    )

    # ------------------------------------------
    # RESULTS
    # ------------------------------------------

    print("\n" + "=" * 70)
    print("STANDARDIZED MOVEMENT TYPES")
    print("=" * 70)

    print(
        df["movement_type"]
        .value_counts(dropna=False)
        .to_string()
    )

    print("\n" + "=" * 70)
    print("STANDARDIZED MATERIAL TYPES")
    print("=" * 70)

    print(
        df["material"]
        .value_counts(dropna=False)
        .to_string()
    )

    # ------------------------------------------
    # SAVE
    # ------------------------------------------

    df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\n" + "=" * 70)
    print("STANDARDIZATION COMPLETE")
    print("=" * 70)

    print(f"\nTotal records: {len(df)}")

    print("\nSaved standardized dataset:")

    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()