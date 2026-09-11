from pathlib import Path

import pandas as pd


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

INPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "landslide_inventory_raw.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "landslide_inventory_clean.csv"
)


# --------------------------------------------------
# NER STATES
# --------------------------------------------------

NER_STATES = [
    "Assam",
    "Arunachal Pradesh",
    "Meghalaya",
    "Manipur",
    "Mizoram",
    "Nagaland",
    "Tripura",
    "Sikkim",
]


def main():

    print("=" * 65)
    print("NER LandslideAI - Landslide Inventory Cleaning")
    print("=" * 65)

    # --------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------

    if not INPUT_PATH.exists():
        print("\nERROR: Raw CSV file not found!")
        print(INPUT_PATH)
        return

    print("\nLoading raw dataset...")

    df = pd.read_csv(INPUT_PATH)

    print(f"Total raw records: {len(df)}")

    print("\nOriginal columns:")
    print(list(df.columns))

    # --------------------------------------------------
    # REMOVE INVALID HEADER ROWS
    # --------------------------------------------------

    print("\nRemoving invalid rows...")

    df = df[
        df["Sl.No."].notna()
    ]

    # Remove rows that are not actual landslide records
    df = df[
        df["Sl.No."].astype(str).str.strip().str.lower()
        != "landslide inventory (field vaidated)"
    ]

    # --------------------------------------------------
    # CLEAN COLUMN NAMES
    # --------------------------------------------------

    df = df.rename(
        columns={
            "Sl.No.": "serial_no",
            "Slide_No": "slide_id",
            "State": "state",
            "District": "district",
            "Slide_Name": "slide_name",
            "NH_SH_Location": "road_location",
            "Latitude": "latitude",
            "Longitude": "longitude",
            "Material Involved": "material",
            "Movement Type": "movement_type",
            "History": "history",
        }
    )

    # --------------------------------------------------
    # CLEAN TEXT COLUMNS
    # --------------------------------------------------

    text_columns = [
        "slide_id",
        "state",
        "district",
        "slide_name",
        "road_location",
        "material",
        "movement_type",
        "history",
    ]

    for column in text_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .astype(str)
                .str.strip()
            )

            df[column] = df[column].replace(
                {
                    "nan": None,
                    "None": None,
                    "": None,
                }
            )

    # --------------------------------------------------
    # CONVERT COORDINATES
    # --------------------------------------------------

    print("Cleaning latitude and longitude...")

    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce"
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce"
    )

    # --------------------------------------------------
    # REMOVE INVALID COORDINATES
    # --------------------------------------------------

    before_coordinates = len(df)

    df = df.dropna(
        subset=[
            "latitude",
            "longitude",
        ]
    )

    # Valid India coordinate range
    df = df[
        df["latitude"].between(6, 38)
        &
        df["longitude"].between(68, 98)
    ]

    print(
        f"Records after coordinate cleaning: {len(df)}"
    )

    print(
        f"Removed invalid coordinates: "
        f"{before_coordinates - len(df)}"
    )

    # --------------------------------------------------
    # CLEAN STATE NAMES
    # --------------------------------------------------

    df["state"] = (
        df["state"]
        .str.replace(
            r"\s+",
            " ",
            regex=True
        )
        .str.strip()
    )

    # --------------------------------------------------
    # FILTER NER STATES
    # --------------------------------------------------

    print("\nFiltering North Eastern Region...")

    before_ner = len(df)

    df = df[
        df["state"].isin(NER_STATES)
    ]

    print(
        f"NER records found: {len(df)}"
    )

    print(
        f"Non-NER records removed: "
        f"{before_ner - len(df)}"
    )

    # --------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------

    before_duplicates = len(df)

    df = df.drop_duplicates(
        subset=[
            "slide_id",
            "latitude",
            "longitude",
        ]
    )

    print(
        f"Duplicate records removed: "
        f"{before_duplicates - len(df)}"
    )

    # --------------------------------------------------
    # RESET INDEX
    # --------------------------------------------------

    df = df.reset_index(
        drop=True
    )

    # --------------------------------------------------
    # SAVE CLEAN DATA
    # --------------------------------------------------

    df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    # --------------------------------------------------
    # DATA SUMMARY
    # --------------------------------------------------

    print("\n" + "=" * 65)
    print("CLEANING COMPLETE")
    print("=" * 65)

    print(
        f"\nFinal clean NER records: {len(df)}"
    )

    print("\nRecords by state:\n")

    print(
        df["state"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nMissing values:\n")

    print(
        df.isnull()
        .sum()
        .to_string()
    )

    print("\nDataset preview:\n")

    print(
        df.head(10)
        .to_string()
    )

    print("\nSaved clean dataset:")

    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()