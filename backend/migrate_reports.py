import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent / "ner_landslideai.db"


def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def add_column(cursor, table, column, definition):
    if not column_exists(cursor, table, column):
        print(f"Adding column: {column}")

        cursor.execute(
            f"ALTER TABLE {table} "
            f"ADD COLUMN {column} {definition}"
        )

    else:
        print(f"Column already exists: {column}")


def main():

    if not DB_PATH.exists():
        print("Database not found:", DB_PATH)
        return

    connection = sqlite3.connect(DB_PATH)

    cursor = connection.cursor()

    print("Checking reports table...")

    add_column(
        cursor,
        "reports",
        "client_report_id",
        "VARCHAR(100)",
    )

    add_column(
        cursor,
        "reports",
        "is_offline_report",
        "BOOLEAN DEFAULT 0",
    )

    add_column(
        cursor,
        "reports",
        "offline_created_at",
        "DATETIME",
    )

    add_column(
        cursor,
        "reports",
        "synced_at",
        "DATETIME",
    )

    connection.commit()

    connection.close()

    print("\nReports database migration completed successfully!")


if __name__ == "__main__":
    main()