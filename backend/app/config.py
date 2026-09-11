"""Application configuration.

Paths are anchored to the repository so the backend works no matter which
working directory uvicorn is started from.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]   # .../NER-LandslideAI/backend
BACKEND_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BACKEND_DIR / "uploads"

# Default: SQLite for local development.
# To move to PostgreSQL/PostGIS later set DATABASE_URL, e.g.:
#   postgresql+psycopg2://user:pass@localhost/landslide_db
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'ner_landslideai.db'}")

# Demo mode: allows road/report verification updates without a login token so
# live demonstrations in front of judges never break. Set OPEN_DEMO_MODE=0
# (or remove the env var) in production to enforce authentication.
OPEN_DEMO_MODE = os.environ.get("OPEN_DEMO_MODE", "1") != "0"

# Secret used to sign access tokens (change in production).
SECRET_KEY = os.environ.get("SECRET_KEY", "ner-landslideai-demo-secret-change-me")
TOKEN_TTL_HOURS = 24

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
# Video upload settings
MAX_VIDEO_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".webm",
}
