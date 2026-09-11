from pathlib import Path
import os
import requests


BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR / "data" / "dem"


API_KEY = os.getenv("OPENTOPOGRAPHY_API_KEY")


# Split NER into smaller regions
REGIONS = [

    {
        "name": "ner_west",
        "south": 21.5,
        "north": 25.5,
        "west": 88.0,
        "east": 92.75,
    },

    {
        "name": "ner_east",
        "south": 21.5,
        "north": 25.5,
        "west": 92.75,
        "east": 97.5,
    },

    {
        "name": "ner_north_west",
        "south": 25.5,
        "north": 29.5,
        "west": 88.0,
        "east": 92.75,
    },

    {
        "name": "ner_north_east",
        "south": 25.5,
        "north": 29.5,
        "west": 92.75,
        "east": 97.5,
    },

]


def download_region(region):

    name = region["name"]

    output_file = (
        OUTPUT_DIR / f"{name}_srtm30.tif"
    )

    url = (
        "https://portal.opentopography.org/API/globaldem"
    )

    params = {
        "demtype": "SRTMGL1",
        "south": region["south"],
        "north": region["north"],
        "west": region["west"],
        "east": region["east"],
        "outputFormat": "GTiff",
        "API_Key": API_KEY,
    }

    print("\n" + "=" * 60)

    print(f"Downloading: {name}")

    print(
        f"Latitude: "
        f"{region['south']} → {region['north']}"
    )

    print(
        f"Longitude: "
        f"{region['west']} → {region['east']}"
    )

    response = requests.get(
        url,
        params=params,
        stream=True,
        timeout=600,
    )

    print(
        f"Server response: "
        f"{response.status_code}"
    )

    if response.status_code != 200:

        print(
            f"\nFAILED: {name}"
        )

        print(
            response.text[:500]
        )

        return False

    total_size = int(
        response.headers.get(
            "content-length",
            0,
        )
    )

    downloaded = 0

    with open(
        output_file,
        "wb",
    ) as file:

        for chunk in response.iter_content(
            chunk_size=1024 * 1024
        ):

            if chunk:

                file.write(chunk)

                downloaded += len(chunk)

                if total_size:

                    percent = (
                        downloaded /
                        total_size
                    ) * 100

                    print(
                        f"\rProgress: "
                        f"{percent:.1f}%",
                        end=""
                    )

    print("\n")

    print(
        f"Saved: {output_file.name}"
    )

    print(
        f"Size: "
        f"{output_file.stat().st_size / (1024 * 1024):.2f} MB"
    )

    return True


def main():

    print("=" * 60)

    print(
        "NER LandslideAI - "
        "SRTM 30m DEM Download"
    )

    print("=" * 60)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not API_KEY:

        print(
            "\nERROR: API key not found."
        )

        print(
            "\nRun:"
        )

        print(
            '$env:OPENTOPOGRAPHY_API_KEY="YOUR_KEY"'
        )

        return

    successful = 0

    for region in REGIONS:

        result = download_region(
            region
        )

        if result:

            successful += 1

    print("\n" + "=" * 60)

    print("DOWNLOAD PROCESS COMPLETE")

    print("=" * 60)

    print(
        f"\nSuccessful downloads: "
        f"{successful}/{len(REGIONS)}"
    )

    print("\nDEM folder:")

    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()