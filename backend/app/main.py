"""NER LandslideAI - FastAPI application entry point.

Run locally:
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000   (from inside backend/)
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import UPLOAD_DIR
from .database import SessionLocal, init_db

APP_NAME = "NER LandslideAI"
APP_DESCRIPTION = (
    "AI-powered landslide early warning and monitoring system for the "
    "North Eastern Region of India - disaster management prototype."
)


def _seed_if_empty() -> None:
    from .models import Location
    from .services.seed import seed_database

    db = SessionLocal()
    try:
        if db.query(Location).count() == 0:
            seed_database(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    _seed_if_empty()
    yield


app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for the React/Vite frontend (development server + LAN/other origins).
# Tighten this list before any production deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------- routers
from .api import (  # noqa: E402  (registered after app creation)
    alerts,
    auth,
    dashboard,
    emergency,
    environment,
    locations,
    reports,
    risk,
    roads,
    simulation,
)

API_PREFIX = "/api"

for module in (auth, locations, environment, risk, reports, roads,
               alerts, emergency, simulation, dashboard):
    app.include_router(module.router, prefix=API_PREFIX)


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "healthy", "message": "NER LandslideAI backend is running"}


@app.get("/", tags=["system"])
def root():
    return {
        "name": APP_NAME,
        "docs": "/docs",
        "health": "/api/health",
        "api": "/api",
    }


# Serve uploaded report images.
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
