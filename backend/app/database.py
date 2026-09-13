"""SQLAlchemy database bootstrap."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL


class Base(DeclarativeBase):
    pass


connect_args = (
    {"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {}
)


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    """FastAPI dependency that yields a database session."""

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def _add_column_if_missing(
    table_name: str,
    column_name: str,
    column_definition: str,
):
    """
    Small SQLite migration helper.

    Adds a column only if it does not already exist.
    """

    if not DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as connection:

        columns = connection.execute(
            text(f"PRAGMA table_info({table_name})")
        ).fetchall()

        existing_columns = {
            column[1]
            for column in columns
        }

        if column_name not in existing_columns:

            connection.execute(
                text(
                    f"ALTER TABLE {table_name} "
                    f"ADD COLUMN {column_name} "
                    f"{column_definition}"
                )
            )

            print(
                f"Database migration: "
                f"added {column_name} "
                f"to {table_name}"
            )


def init_db():
    """Create tables and safely apply small database upgrades."""

    # Import registers all ORM models.
    from . import models  # noqa: F401

    # Create new tables.
    Base.metadata.create_all(
        bind=engine
    )

    # ======================================================
    # DATABASE MIGRATIONS
    # ======================================================

    # ------------------------------------------------------
    # USER UPGRADES
    # ------------------------------------------------------

    _add_column_if_missing(
        table_name="users",
        column_name="preferred_language",
        column_definition=(
            "VARCHAR(10) NOT NULL DEFAULT 'EN'"
        ),
    )

    # ------------------------------------------------------
    # REPORT UPGRADES
    # ------------------------------------------------------

    _add_column_if_missing(
        table_name="reports",
        column_name="client_report_id",
        column_definition="VARCHAR(100)",
    )

    _add_column_if_missing(
        table_name="reports",
        column_name="video_path",
        column_definition="VARCHAR(300)",
    )

    _add_column_if_missing(
        table_name="reports",
        column_name="severity",
        column_definition=(
            "VARCHAR(20) NOT NULL DEFAULT 'MODERATE'"
        ),
    )

    _add_column_if_missing(
        table_name="reports",
        column_name="location_id",
        column_definition="INTEGER",
    )

    _add_column_if_missing(
        table_name="reports",
        column_name="is_offline_report",
        column_definition=(
            "BOOLEAN NOT NULL DEFAULT 0"
        ),
    )

    _add_column_if_missing(
        table_name="reports",
        column_name="offline_created_at",
        column_definition="DATETIME",
    )

    _add_column_if_missing(
        table_name="reports",
        column_name="synced_at",
        column_definition="DATETIME",
    )

    _add_column_if_missing(
        table_name="reports",
        column_name="verified_at",
        column_definition="DATETIME",
    )