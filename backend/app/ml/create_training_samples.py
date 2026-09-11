from pathlib import Path
import random
import math

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent

INPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "landslide_inventory_standardized.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "landslide_training_samples.csv"
)


NER_BOUNDS = {
    "min_lat": 21.5,
    "max_lat": 29.5,
    "min_lon": 88.0,
    "max_lon": 97.5,
}


def distance_in_degrees(lat1, lon1, lat2, lon2):

    return math.sqrt(
        (lat1 - lat2) ** 2
        +
        (lon1 - lon2) ** 2
    )


def generate_background_samples(
    positive_df,
    count,
    min_distance=0.05,
    min_offset=0.08,
    max_offset=0.30,
):

    samples = []

    coordinates = list(
        zip(
            positive_df["latitude"],
            positive_df["longitude"],
        )
    )

    attempts = 0
    max_attempts = count * 100

    while (
        len(samples) < count
        and attempts < max_attempts
    ):

        attempts += 1

        # Select a real landslide location
        base_lat, base_lon = random.choice(
            coordinates
        )

        # Generate random direction
        angle = random.uniform(
            0,
            2 * math.pi,
        )

        # Generate random offset
        offset = random.uniform(
            min_offset,
            max_offset,
        )

        # Generate candidate coordinates
        lat = (
            base_lat
            +
            offset * math.cos(angle)
        )

        lon = (
            base_lon
            +
            offset * math.sin(angle)
        )

        # Keep candidate inside NER bounds
        if not (
            NER_BOUNDS["min_lat"]
            <= lat
            <= NER_BOUNDS["max_lat"]

            and

            NER_BOUNDS["min_lon"]
            <= lon
            <= NER_BOUNDS["max_lon"]
        ):
            continue

        # Check distance from known landslides
        is_far_enough = True

        for known_lat, known_lon in coordinates:

            distance = distance_in_degrees(
                lat,
                lon,
                known_lat,
                known_lon,
            )

            if distance < min_distance:

                is_far_enough = False
                break

        # Add background sample
        if is_far_enough:

            samples.append(
                {
                    "latitude": lat,
                    "longitude": lon,
                    "state": None,
                    "district": None,
                    "label": 0,
                }
            )

        if attempts % 1000 == 0:

            print(
                f"Attempts: {attempts} | "
                f"Background samples: "
                f"{len(samples)}"
            )

    return pd.DataFrame(samples)


def main():

    print("=" * 70)
    print(
        "NER LandslideAI - Improved Training Sample Creation"
    )
    print("=" * 70)

    if not INPUT_PATH.exists():

        print(
            "\nERROR: Standardized dataset not found!"
        )

        print(INPUT_PATH)

        return

    # Load inventory

    print("\nLoading landslide inventory...")

    df = pd.read_csv(INPUT_PATH)

    print(
        f"Total inventory records: {len(df)}"
    )

    # Create positive samples

    positive_df = df[
        [
            "latitude",
            "longitude",
            "state",
            "district",
        ]
    ].copy()

    positive_df = positive_df.drop_duplicates(
        subset=[
            "latitude",
            "longitude",
        ]
    )

    positive_df["label"] = 1

    print(
        f"Unique positive samples: "
        f"{len(positive_df)}"
    )

    # Generate background samples

    background_count = len(positive_df)

    print(
        f"\nGenerating {background_count} "
        f"NER background samples..."
    )

    background_df = generate_background_samples(
        positive_df,
        background_count,
    )

    print(
        f"\nBackground samples generated: "
        f"{len(background_df)}"
    )

    # Combine datasets

    training_df = pd.concat(
        [
            positive_df,
            background_df,
        ],
        ignore_index=True,
    )

    # Shuffle

    training_df = training_df.sample(
        frac=1,
        random_state=42,
    ).reset_index(
        drop=True
    )

    # Save

    training_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("\n" + "=" * 70)
    print(
        "TRAINING SAMPLE CREATION COMPLETE"
    )
    print("=" * 70)

    print(
        f"\nPositive samples: "
        f"{len(positive_df)}"
    )

    print(
        f"Background samples: "
        f"{len(background_df)}"
    )

    print(
        f"Total samples: "
        f"{len(training_df)}"
    )

    print("\nLabel distribution:")

    print(
        training_df["label"]
        .value_counts()
        .to_string()
    )

    print("\nCoordinate range:")

    print(
        f"Latitude: "
        f"{training_df['latitude'].min()} "
        f"to "
        f"{training_df['latitude'].max()}"
    )

    print(
        f"Longitude: "
        f"{training_df['longitude'].min()} "
        f"to "
        f"{training_df['longitude'].max()}"
    )

    print("\nSaved training samples:")

    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()