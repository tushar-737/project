from pathlib import Path

import pdfplumber
import pandas as pd


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

PDF_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "landslide_report.pdf"
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "landslide_inventory_raw.csv"
)


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def clean_cell(value):
    """Clean extracted PDF cell values."""

    if value is None:
        return ""

    return str(value).replace("\n", " ").strip()


def looks_like_landslide_row(row):
    """
    Check whether a row appears to be
    an actual landslide inventory record.
    """

    text = " ".join(
        clean_cell(cell).lower()
        for cell in row
        if cell
    )

    keywords = [
        "slide",
        "landslide",
        "debris",
        "rock",
    ]

    return any(keyword in text for keyword in keywords)


def is_header_row(row):
    """Detect table header rows."""

    text = " ".join(
        clean_cell(cell).lower()
        for cell in row
        if cell
    )

    header_keywords = [
        "sl.no",
        "slide_no",
        "state",
        "district",
        "latitude",
        "longitude",
        "slide_name",
    ]

    matches = sum(
        keyword in text
        for keyword in header_keywords
    )

    return matches >= 3


# --------------------------------------------------
# MAIN EXTRACTION
# --------------------------------------------------

def main():

    print("=" * 70)
    print("NER LandslideAI - Complete Landslide Inventory Extraction")
    print("=" * 70)

    if not PDF_PATH.exists():

        print("\nPDF not found!")

        print(PDF_PATH)

        return


    print(f"\nPDF found:")
    print(PDF_PATH)


    rows = []

    pages_with_tables = []

    header = None


    with pdfplumber.open(PDF_PATH) as pdf:

        total_pages = len(pdf.pages)

        print(f"\nTotal pages: {total_pages}")

        print("\nScanning complete PDF...\n")


        for i, page in enumerate(pdf.pages):

            page_number = i + 1


            # Progress message every 25 pages
            if page_number % 25 == 0 or page_number == 1:

                print(
                    f"Processing page "
                    f"{page_number}/{total_pages}"
                )


            try:

                tables = page.extract_tables()


                if not tables:

                    continue


                pages_with_tables.append(page_number)


                for table in tables:


                    for row in table:


                        if not row:

                            continue


                        cleaned_row = [

                            clean_cell(cell)

                            for cell in row

                        ]


                        # Skip completely empty rows

                        if not any(cleaned_row):

                            continue


                        # Detect header

                        if is_header_row(cleaned_row):

                            if header is None:

                                header = cleaned_row

                                print(
                                    f"\nInventory header found "
                                    f"on page {page_number}"
                                )

                            continue


                        # Keep probable landslide rows

                        if looks_like_landslide_row(cleaned_row):

                            rows.append(cleaned_row)


            except Exception as e:

                print(
                    f"\nWarning: Error processing "
                    f"page {page_number}: {e}"
                )


    # --------------------------------------------------
    # RESULTS
    # --------------------------------------------------

    print("\n" + "=" * 70)

    print("EXTRACTION COMPLETE")

    print("=" * 70)


    print(
        f"\nPages containing tables: "
        f"{len(pages_with_tables)}"
    )


    print(
        f"Total landslide rows extracted: "
        f"{len(rows)}"
    )


    if not rows:

        print("\nNo landslide inventory rows found!")

        return


    # --------------------------------------------------
    # NORMALIZE COLUMN LENGTH
    # --------------------------------------------------

    max_columns = max(

        len(row)

        for row in rows

    )


    normalized_rows = []


    for row in rows:


        row = list(row)


        while len(row) < max_columns:

            row.append("")


        normalized_rows.append(row)


    # --------------------------------------------------
    # CREATE DATAFRAME
    # --------------------------------------------------

    if header and len(header) == max_columns:

        columns = header


    else:

        columns = [

            f"column_{i}"

            for i in range(max_columns)

        ]


    df = pd.DataFrame(

        normalized_rows,

        columns=columns

    )


    # --------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------

    before = len(df)


    df = df.drop_duplicates()


    after = len(df)


    print(

        f"\nDuplicate rows removed: "

        f"{before - after}"

    )


    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------

    OUTPUT_PATH.parent.mkdir(

        parents=True,

        exist_ok=True

    )


    df.to_csv(

        OUTPUT_PATH,

        index=False,

        encoding="utf-8"

    )


    print("\nSaved file:")

    print(OUTPUT_PATH)


    # --------------------------------------------------
    # PREVIEW
    # --------------------------------------------------

    print("\nDATA PREVIEW:\n")


    print(

        df.head(15).to_string()

    )


    print(

        f"\nTotal final records: "

        f"{len(df)}"

    )


    print("\nColumns:")

    print(

        list(df.columns)

    )


if __name__ == "__main__":

    main()