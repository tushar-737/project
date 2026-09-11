from pathlib import Path
import math
import pandas as pd


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
    / "required_dem_tiles.txt"
)


def get_tile_name(latitude, longitude):
    """
    Convert latitude/longitude into an SRTM tile name.

    Example:
    24.27, 92.50 -> N24E092
    """

    lat = math.floor(latitude)
    lon = math.floor(longitude)

    lat_prefix = "N" if lat >= 0 else "S"
    lon_prefix = "E" if lon >= 0 else "W"

    return (
        f"{lat_prefix}{abs(lat):02d}"
        f"{lon_prefix}{abs(lon):03d}"
    )


def main():

    print("=" * 60)
    print("NER LandslideAI - DEM Tile Finder")
    print("=" * 60)

    print("\nLoading training samples...")

    df = pd.read_csv(INPUT_PATH)

    print(f"Total samples: {len(df)}")

    print("\nFinding required DEM tiles...")

    tiles = set()

    for _, row in df.iterrows():

        tile = get_tile_name(
            row["latitude"],
            row["longitude"],
        )

        tiles.add(tile)

    tiles = sorted(tiles)

    print(f"\nTotal unique DEM tiles required: {len(tiles)}")

    print("\nRequired tiles:\n")

    for tile in tiles:
        print(tile)

    with open(OUTPUT_PATH, "w") as file:

        for tile in tiles:
            file.write(tile + "\n")

    print("\n" + "=" * 60)
    print("TILE FINDING COMPLETE")
    print("=" * 60)

    print(f"\nTile list saved to:\n{OUTPUT_PATH}")


if __name__ == "__main__":
    main()