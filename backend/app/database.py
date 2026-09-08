"""SQLAlchemy database bootstrap.

SQLite is used for the local prototype. The engine is created purely from the
DATABASE_URL setting (see config.py), so pointing the app at PostgreSQL is a
configuration change and requires no code changes.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables and (on first run) seed demo data."""
    from . import models  # noqa: F401  (import registers all ORM models)

    Base.metadata.create_all(bind=engine)
