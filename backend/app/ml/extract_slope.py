from pathlib import Path
import math

import numpy as np
import pandas as pd
import rasterio


BASE_DIR = Path(__file__).resolve().parent


INPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "landslide_training_with_elevation.csv"
)


OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "landslide_training_with_terrain.csv"
)


DEM_DIR = BASE_DIR / "data" / "dem"


DEM_FILES = [
    "ner_west_srtm30.tif",
    "ner_east_srtm30.tif",
    "ner_north_west_srtm30.tif",
    "ner_north_east_srtm30.tif",
]


def get_slope(latitude, longitude, datasets):

    """
    Calculate terrain slope in degrees using
    neighbouring DEM elevation pixels.
    """

    for dataset in datasets:

        try:

            row, col = dataset.index(
                longitude,
                latitude,
            )

            # Make sure surrounding pixels exist
            if (
                row < 1
                or col < 1
                or row >= dataset.height - 1
                or col >= dataset.width - 1
            ):
                continue

            # Read 3x3 elevation window
            window = rasterio.windows.Window(
                col - 1,
                row - 1,
                3,
                3,
            )

            elevation = dataset.read(
                1,
                window=window,
            ).astype(float)

            if elevation.shape != (3, 3):
                continue

            # Check for invalid values
            if np.any(np.isnan(elevation)):
                continue

            if dataset.nodata is not None:

                if np.any(
                    elevation == dataset.nodata
                ):
                    continue

            # Pixel size in degrees
            x_resolution = abs(
                dataset.transform.a
            )

            y_resolution = abs(
                dataset.transform.e
            )

            # Convert degrees to metres
            latitude_rad = math.radians(
                latitude
            )

            metres_per_degree_lat = (
                111320
            )

            metres_per_degree_lon = (
                111320
                * math.cos(latitude_rad)
            )

            pixel_x = (
                x_resolution
                * metres_per_degree_lon
            )

            pixel_y = (
                y_resolution
                * metres_per_degree_lat
            )

            # Horn's method
            dz_dx = (

                (
                    elevation[0, 2]
                    + 2 * elevation[1, 2]
                    + elevation[2, 2]
                    -
                    elevation[0, 0]
                    - 2 * elevation[1, 0]
                    - elevation[2, 0]
                )

                /
                (8 * pixel_x)

            )

            dz_dy = (

                (
                    elevation[2, 0]
                    + 2 * elevation[2, 1]
                    + elevation[2, 2]
                    -
                    elevation[0, 0]
                    - 2 * elevation[0, 1]
                    - elevation[0, 2]
                )

                /
                (8 * pixel_y)

            )

            slope_radians = math.atan(
                math.sqrt(
                    dz_dx ** 2
                    +
                    dz_dy ** 2
                )
            )

            slope_degrees = math.degrees(
                slope_radians
            )

            return round(
                slope_degrees,
                2,
            )

        except Exception:

            continue

    return None


def main():

    print("=" * 70)
    print(
        "NER LandslideAI - "
        "Terrain Slope Extraction"
    )
    print("=" * 70)


    # Check dataset

    if not INPUT_PATH.exists():

        print(
            "\nERROR: Elevation dataset not found!"
        )

        print(INPUT_PATH)

        return


    # Load dataset

    print(
        "\nLoading training dataset..."
    )

    df = pd.read_csv(
        INPUT_PATH
    )

    print(
        f"Total samples: {len(df)}"
    )


    # Load DEMs

    print(
        "\nLoading DEM datasets..."
    )

    datasets = []


    for filename in DEM_FILES:

        path = DEM_DIR / filename


        if not path.exists():

            print(
                f"\nWARNING: Missing DEM: "
                f"{filename}"
            )

            continue


        print(
            f"Loading: {filename}"
        )

        datasets.append(
            rasterio.open(path)
        )


    print(
        f"\nDEM datasets loaded: "
        f"{len(datasets)}"
    )


    if not datasets:

        print(
            "\nERROR: No DEM datasets found!"
        )

        return


    # Calculate slopes

    print(
        "\nCalculating terrain slopes..."
    )


    slopes = []


    for index, row in df.iterrows():

        slope = get_slope(

            row["latitude"],
            row["longitude"],
            datasets,

        )

        slopes.append(slope)


        if (index + 1) % 500 == 0:

            print(
                f"Processed: "
                f"{index + 1}/{len(df)}"
            )


    # Add slope column

    df["slope_angle"] = slopes


    # Close DEM files

    for dataset in datasets:

        dataset.close()


    # Statistics

    missing = (
        df["slope_angle"]
        .isna()
        .sum()
    )


    print("\n" + "=" * 70)
    print(
        "SLOPE EXTRACTION COMPLETE"
    )
    print("=" * 70)


    print(
        f"\nTotal samples: {len(df)}"
    )

    print(
        f"Slope values found: "
        f"{len(df) - missing}"
    )

    print(
        f"Missing slope values: "
        f"{missing}"
    )


    if missing < len(df):

        print(
            "\nSlope statistics:"
        )

        print(
            df["slope_angle"]
            .describe()
            .to_string()
        )


    # Save

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )


    print(
        "\nSaved dataset:"
    )

    print(
        OUTPUT_PATH
    )


if __name__ == "__main__":
    main()