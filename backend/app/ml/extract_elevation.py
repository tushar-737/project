from pathlib import Path

import pandas as pd
import rasterio


BASE_DIR = Path(__file__).resolve().parent


INPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "landslide_training_samples.csv"
)


OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "landslide_training_with_elevation.csv"
)


DEM_DIR = (
    BASE_DIR
    / "data"
    / "dem"
)


DEM_FILES = [
    "ner_west_srtm30.tif",
    "ner_east_srtm30.tif",
    "ner_north_west_srtm30.tif",
    "ner_north_east_srtm30.tif",
]


def get_elevation(latitude, longitude, datasets):

    """
    Find elevation for a latitude/longitude point.

    The function checks each DEM dataset until
    it finds the dataset containing the point.
    """

    for dataset in datasets:

        try:

            row, col = dataset.index(
                longitude,
                latitude,
            )

            if (
                0 <= row < dataset.height
                and
                0 <= col < dataset.width
            ):

                value = dataset.read(
                    1,
                    window=(
                        (row, row + 1),
                        (col, col + 1),
                    ),
                )[0][0]

                if dataset.nodata is not None:

                    if value == dataset.nodata:

                        continue

                return float(value)

        except Exception:

            continue

    return None


def main():

    print("=" * 70)

    print(
        "NER LandslideAI - "
        "Elevation Feature Extraction"
    )

    print("=" * 70)


    # --------------------------------------------------
    # CHECK FILES
    # --------------------------------------------------

    if not INPUT_PATH.exists():

        print("\nERROR: Training samples file not found!")

        print(INPUT_PATH)

        return


    print("\nLoading training samples...")

    df = pd.read_csv(INPUT_PATH)

    print(
        f"Total samples: {len(df)}"
    )


    # --------------------------------------------------
    # LOAD DEM FILES
    # --------------------------------------------------

    print("\nLoading DEM datasets...")

    datasets = []

    for filename in DEM_FILES:

        path = DEM_DIR / filename

        if not path.exists():

            print(
                f"\nWARNING: DEM file not found: "
                f"{filename}"
            )

            continue


        print(
            f"Loading: {filename}"
        )

        dataset = rasterio.open(path)

        datasets.append(dataset)


    print(
        f"\nDEM datasets loaded: "
        f"{len(datasets)}"
    )


    if not datasets:

        print(
            "\nERROR: No DEM datasets available!"
        )

        return


    # --------------------------------------------------
    # EXTRACT ELEVATION
    # --------------------------------------------------

    print(
        "\nExtracting elevation values..."
    )


    elevations = []


    for index, row in df.iterrows():

        elevation = get_elevation(

            row["latitude"],
            row["longitude"],
            datasets,

        )

        elevations.append(elevation)


        if (index + 1) % 500 == 0:

            print(
                f"Processed: "
                f"{index + 1}/{len(df)}"
            )


    # --------------------------------------------------
    # ADD ELEVATION
    # --------------------------------------------------

    df["elevation"] = elevations


    # --------------------------------------------------
    # CLOSE DEM FILES
    # --------------------------------------------------

    for dataset in datasets:

        dataset.close()


    # --------------------------------------------------
    # ANALYSIS
    # --------------------------------------------------

    missing = df["elevation"].isna().sum()


    print("\n" + "=" * 70)

    print(
        "ELEVATION EXTRACTION COMPLETE"
    )

    print("=" * 70)


    print(
        f"\nTotal samples: {len(df)}"
    )

    print(
        f"Elevation values found: "
        f"{len(df) - missing}"
    )

    print(
        f"Missing elevation values: "
        f"{missing}"
    )


    if missing < len(df):

        print("\nElevation statistics:")

        print(
            df["elevation"]
            .describe()
            .to_string()
        )


    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------

    df.to_csv(

        OUTPUT_PATH,

        index=False,

    )


    print("\nSaved dataset:")

    print(OUTPUT_PATH)


if __name__ == "__main__":

    main()