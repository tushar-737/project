"""NER LandslideAI - FastAPI application entry point."""

from contextlib import asynccontextmanager

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


# CORS for the React/Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
from .api import (
    alerts,
    auth,
    dashboard,
    emergency,
    environment,
    gis,
    locations,
    reports,
    risk,
    roads,
    simulation,
    ml,
)


API_PREFIX = "/api"


for module in (
    auth,
    locations,
    environment,
    risk,
    reports,
    roads,
    alerts,
    emergency,
    simulation,
    dashboard,
    gis,
    ml,
):
    app.include_router(module.router, prefix=API_PREFIX)


@app.get("/api/health", tags=["system"])
def health():
    return {
        "status": "healthy",
        "message": "NER LandslideAI backend is running",
    }


@app.get("/", tags=["system"])
def root():
    return {
        "name": APP_NAME,
        "docs": "/docs",
        "health": "/api/health",
        "api": "/api",
    }


# Serve uploaded report images
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")