# 🚨 NER LandslideAI

**AI-Powered Landslide Early Warning & Monitoring System for the North Eastern Region of India**

A working full-stack prototype (FastAPI + SQLite + React) for disaster management: it simulates environmental sensors, runs an AI risk engine, visualizes live landslide risk on a GIS map, collects field reports, monitors road connectivity, and automatically generates alerts + emergency response priorities.

> ⚠️ **Scope note:** this system predicts landslide **risk / probability** (0–100 over the current 24h window). It does **not** predict the exact time of a landslide event.

![stack](https://img.shields.io/badge/backend-FastAPI%20%2B%20SQLAlchemy-009688) ![stack](https://img.shields.io/badge/ai-hybrid%20rule%20engine%20%2B%20ML--ready-1565c0) ![stack](https://img.shields.io/badge/frontend-React%20%2B%20Vite%20%2B%20Tailwind-61dafb) ![stack](https://img.shields.io/badge/gis-Leaflet%20%2B%20OSM-4caf50) ![stack](https://img.shields.io/badge/charts-Recharts-f97316)

---

## Table of contents

1. [Features](#features)
2. [How the warning pipeline works](#how-the-warning-pipeline-works)
3. [Architecture](#architecture)
4. [Technology stack](#technology-stack)
5. [Project structure](#project-structure)
6. [Installation & setup](#installation--setup)
7. [Demo mode](#demo-mode)
8. [Sensor simulation](#sensor-simulation)
9. [API reference](#api-reference)
10. [Future IoT integration](#future-iot-integration)
11. [Future ML integration](#future-ml-integration)
12. [Testing](#testing)
13. [FAQ](#faq)

---

## Features

| Area | What the prototype does |
|---|---|
| 📡 **Sensor simulation** | Simulated rainfall, soil moisture, temperature, humidity & slope with 4 weather scenarios (`NORMAL`, `MODERATE_RAIN`, `HEAVY_RAIN`, `EXTREME_RAIN`) — no hardware needed |
| 🧠 **AI risk engine** | Hybrid rule-based engine (rainfall 30% · soil moisture 25% · slope 20% · historical susceptibility 15% · humidity 10% + elevation amplifier) producing a **risk score 0–100** and level **LOW / MODERATE / HIGH / CRITICAL** with confidence + explainable contributing factors |
| 🔁 **Automatic pipeline** | Every new sample automatically → saves environment data → runs risk engine → saves prediction → updates alert state → logs SMS broadcast → recomputes emergency priority |
| 🗺️ **GIS map** | Leaflet + OpenStreetMap focused on the North Eastern Region: colour-coded risk pins (green/yellow/orange/red, red pulses), road polylines with status, field-report markers with photos, district popups with rainfall/soil/slope/risk/last-updated |
| 📝 **Field & citizen reports** | 7 report types, GPS auto-capture with fallback click-on-map, JPG/PNG photo upload (≤ 5 MB), officer verify/reject workflow |
| 🛣️ **Road connectivity** | 10 corridors with `OPEN / HIGH_RISK / PARTIALLY_BLOCKED / BLOCKED` statuses; officers update status in one click and linked emergency priorities re-rank instantly |
| 🚨 **Alert engine** | HIGH (≥ 51) and CRITICAL (≥ 76) bulletins in the mandated format, auto-resolution when risk drops, **simulated SMS broadcast logs** |
| 🚑 **Emergency prioritisation** | PRIORITY 1 / 2 / 3 ranking from risk score (55%) + road isolation (25%) + population (12%) + remoteness (8%) |
| 🧪 **Simulation center** | Pick any location + scenario and watch the 9-step workflow complete live with an animated pipeline, risk gauge, contributing factors, alert card and priority tier |
| 🚨 **One-click demo** | `RUN LANDSLIDE SIMULATION` auto-picks the highest-risk location, simulates EXTREME RAIN and runs the whole DATA → AI → PREDICTION → MAP → ALERT → RESPONSE chain — dashboard/map/alert pages refresh automatically |
| 📊 **Analytics** | Risk distribution, rainfall vs risk & soil vs risk scatter plots, road status & report-type bars, regional 72h risk trend |
| 📉 **Offline reporting** | Field reports (with photos) queue in `localStorage` while offline and auto-sync when the connection returns |
| 🌐 **Bilingual UI** | English & Hindi dictionaries (add more languages in `frontend/src/i18n/`) |
| 🏛️ **Government-grade look** | Dark-blue/white government monitoring console, responsive, no "student project" styling |

**Seed data** (created automatically on first run, deterministic): 27 vulnerable locations across all 8 NE states (Assam, Arunachal Pradesh, Meghalaya, Manipur, Mizoram, Nagaland, Tripura, Sikkim), 10 roads, 10 reports, historical telemetry, current-state risk predictions, active alerts, SMS logs and emergency priorities — a balanced monsoon snapshot (7 CRITICAL / 5 HIGH / 13 MODERATE / 2 LOW).

## How the warning pipeline works

```
Environmental Data  ──►  Data Processing  ──►  AI Risk Analysis  ──►  Risk Score (0-100)
      │                       │                      │                        │
   simulated              validated &            rainfall 30%            LOW  0-25
   sensors or             stored in SQLite       soil 25%                MODERATE 26-50
   future IoT                                   slope 20%                HIGH 51-75
                                                history 15%              CRITICAL 76-100
                                                humidity 10%                  │
                                                                              ▼
Emergency response prioritisation  ◄──  SMS log  ◄──  Alert bulletin  ◄──  High-risk zone
```

`backend/app/services/pipeline.py` orchestrates every step; both the simulator and the future IoT ingestion endpoint feed the exact same pipeline.

## Architecture

```
┌────────────────────────────┐        ┌──────────────────────────────────────────────┐
│   React 18 + Vite + SPA    │  /api  │                FastAPI backend                 │
│   Tailwind · Router ·      │ ─────► │  /api/auth · locations · environment · risk   │
│   Leaflet · Recharts       │ ◄───── │  reports · roads · alerts · emergency ·       │
│   (dev proxy :5173 → :8000)│        │  simulation · dashboard                       │
└────────────────────────────┘        │         │            │              │         │
                                      │         ▼            ▼              ▼         │
                                      │  SensorDataSource ──► RiskEngine  ──► SQLite  │
                                      │  (simulated today,   (rule-based    models    │
                                      │   IoT-ready)          + ML-ready)            │
                                      └──────────────────────────────────────────────┘
```

**Sensor abstraction** (`backend/app/services/sensor_service.py`):

```
SensorDataSource  (abstract interface: .read(location) → SensorSample)
├── SimulatedSensorService   ← used today (deterministic RNG for repeatable demos)
└── RealIoTSensorService     ← future: ESP32/Arduino gateway posting to POST /api/environment/ingest
```

**Risk engine abstraction** (`backend/app/ml/risk_engine.py`): `BaseRiskEngine` → `RuleBasedRiskEngine` (current) with a clearly commented **ML integration point** — swap `get_risk_engine()` to a scikit-learn model trained on historical samples; nothing else changes.

## Technology stack

**Frontend:** React 18 · Vite 5 · JavaScript · Tailwind CSS 3 · React Router 6 · Leaflet + React Leaflet 4 · Recharts 2
**Backend:** Python 3.11 · FastAPI · Uvicorn · Pydantic v2 · SQLAlchemy 2
**Database:** SQLite (file `backend/ner_landslideai.db`, auto-created + seeded). Postgres/PostGIS-ready: set `DATABASE_URL=postgresql+psycopg2://...` — no code changes needed.
**AI/ML:** hybrid engine — a trained scikit-learn `RandomForestClassifier` (terrain susceptibility, from elevation + slope) blended with rule-based rainfall/soil-moisture/historical-factor scoring. See [Installation & setup](#installation--setup) — the trained model file must be generated once before first run.
**No paid services, no physical hardware required.**

## Project structure

```
NER-LandslideAI/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, static /uploads, startup seeding
│   │   ├── config.py          # paths, DATABASE_URL, upload limits
│   │   ├── database.py        # SQLAlchemy engine/session (SQLite → Postgres via URL)
│   │   ├── models/            # ORM: users, locations, environmental_data, risk_predictions,
│   │   │                      #       reports, roads, alerts, emergency_priorities, sms_logs
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── api/               # routers (auth, locations, environment, risk, reports,
│   │   │                      #       roads, alerts, emergency, simulation, dashboard) + deps
│   │   ├── services/          # sensor_service, pipeline, alert_service, sms_service,
│   │   │                      #       emergency_service, seed
│   │   ├── ml/risk_engine.py  # rule engine + ML integration point
│   │   └── utils/             # queries, security (PBKDF2 + signed tokens)
│   ├── uploads/               # report photos (served at /uploads)
│   └── ner_landslideai.db     # SQLite (auto-created, gitignored)
├── frontend/
│   └── src/
│       ├── components/        # Layout, ui primitives, badges, stat cards
│       ├── pages/             # Login, Dashboard, RiskMap, Monitoring, Alerts,
│       │                      # FieldReports, RoadsPage, Emergency, Analytics, SimulationCenter
│       ├── services/          # api client, offline queue
│       ├── context/           # AuthContext
│       ├── hooks/useApi.js    # fetch + polling + refresh
│       ├── i18n/              # en.js, hi.js dictionaries
│       ├── test/              # vitest + jsdom smoke/E2E tests
│       └── utils/             # risk vocab/colors, formatters
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation & setup

Requirements: **Python 3.10+**, **Node 18+**.

### 1 · Backend

```bash
pip install -r requirements.txt     # from the project root
cd backend
python -m app.ml.train_susceptibility_model   # one-time: trains + saves the .joblib model
uvicorn app.main:app --reload --port 8000
```

The training step reads `backend/app/ml/data/processed/landslide_ml_dataset.csv` and writes `backend/app/ml/models/landslide_susceptibility_model.joblib`. This file is git-ignored (it's a trained binary, not source) and **is required at startup** — `LandslideRiskEngine` raises a clear `FileNotFoundError` with this exact command if it's missing, instead of failing silently. Re-run it any time the training data changes; skip it on subsequent runs once the file exists.

First startup creates `backend/ner_landslideai.db` and seeds the full demo dataset automatically (takes ~2 seconds). Interactive API docs: **http://localhost:8000/docs**.

### 2 · Frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — the dev server proxies `/api` and `/uploads` to the backend on :8000.

### 3 · Quick check

```bash
curl http://localhost:8000/api/health
# {"status":"healthy","message":"NER LandslideAI backend is running"}
```

### Demo accounts

| Role | Email | Password |
|---|---|---|
| Administrator | `admin@ner.gov.in` | `admin123` |
| Field Officer | `officer@ner.gov.in` | `officer123` |
| Citizen | `citizen@ner.gov.in` | `citizen123` |

The prototype runs in **open demo mode** by default (`OPEN_DEMO_MODE=1`): pages are usable without logging in (actions act as the admin). Set `OPEN_DEMO_MODE=0` to enforce authentication.

## Demo mode

A 60-second demonstration script for judges/officials:

1. Start backend + frontend (above) and open the dashboard — live counts, distribution chart, recent alerts/reports.
2. Open **Risk Map** → 27 colour-coded locations across the 8 NE states, road corridors, report markers; click Shillong/Aizawl pin → district popup with rainfall, soil moisture, slope, risk score, last updated.
3. Open **Simulation Center** → select *Aizawl* → scenario *EXTREME RAIN* → **RUN SIMULATION**.
   Watch the pipeline steps complete, the risk gauge jump into CRITICAL, the formatted alert bulletin + SMS log id and the emergency tier appear.
4. Click **🚨 RUN LANDSLIDE SIMULATION** (also on the dashboard header) — auto-selects the highest-risk location and repeats the full chain.
5. Switch to the **Dashboard / Alerts / Emergency** pages — they auto-refresh every 15–30 s, so the new CRITICAL alert, updated counts and re-ranked PRIORITY 1 list are visible.
6. (Optional) Open **Field Reports** → New Report → test GPS or click the mini-map → upload a photo → officers verify/reject. Try it again with your network off to see offline queueing.
7. **Road Connectivity** → flip *Aizawl–Lengpui Airport Rd* from BLOCKED to OPEN → the Emergency page re-ranks Aizawl instantly.

## Sensor simulation

`POST /api/simulation/run` accepts:

```json
{ "location_id": 19, "scenario": "EXTREME_RAIN" }
```

Scenario ranges (realistic monsoon values, drawn per-location with tilt):

| Scenario | Rainfall | Soil moisture | Humidity |
|---|---|---|---|
| `NORMAL` | 0–20 mm | 25–55 % | 45–80 % |
| `MODERATE_RAIN` | 20–80 mm | 50–75 % | 65–90 % |
| `HEAVY_RAIN` | 150–300 mm | 70–100 % | 80–100 % |
| `EXTREME_RAIN` | 250–500 mm | 85–100 % | 85–100 % |

Temperature 10–40 °C and slope angle 0–90° are also generated. Every run returns the complete pipeline result (`risk_score`, `risk_level`, `confidence`, `contributing_factors`, `alert_id`, `sms_log_id`, `priority_level`, `pipeline_steps`).

## API reference

Base URL `http://localhost:8000/api` — full interactive docs at `/docs`.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/auth/register` | Create account (name, email, password, role) |
| POST | `/auth/login` | Sign in → bearer token |
| GET | `/auth/me` | Current user |
| GET | `/locations` | All locations + latest environment & risk |
| GET | `/environment/{location_id}` | Telemetry history of a location |
| POST | `/environment/ingest` | ⛓️ IoT gateway hook — runs the full pipeline |
| GET | `/risk/zones` | Current risk overview (filters: `state`, `level`) |
| GET | `/risk/zones/summary` | Counts per risk level |
| GET | `/risk/{location_id}` | Location + env + latest prediction |
| GET | `/risk/{location_id}/history` | Past predictions (trend) |
| GET | `/risk/trend/overview` | Aggregated regional trend (hourly, 72 h) |
| POST | `/reports` | Create report (multipart: type, desc, lat, lon, image ≤5 MB JPG/PNG) |
| GET | `/reports` | List reports (filters: `status`, `report_type`) |
| PUT | `/reports/{id}/verify` | Officer verify/reject |
| GET | `/roads` · `/roads/summary` | Road list / status counts |
| PUT | `/roads/{id}` | Officer status update (re-ranks emergency priorities) |
| GET | `/alerts` · `/alerts/summary` | Alert bulletins / counts |
| PUT | `/alerts/{id}/resolve` | Manually resolve an alert |
| GET | `/emergency/priorities` | Ranked response list |
| POST | `/emergency/recompute` | Recompute full ranking |
| POST | `/simulation/environment` | Generate + store one sample only |
| POST | `/simulation/run` | Full pipeline for a location + scenario |
| POST | `/simulation/run-demo` | One-click EXTREME RAIN on the highest-risk site |
| GET | `/dashboard/summary` | Dashboard payload (counts, distribution, recent alerts/reports, weather outlook, top risk) |
| GET | `/uploads/{file}` | Served report images |

## Future IoT integration

1. Hardware: rain gauge + soil-moisture probe + DHT22 on ESP32/Arduino → POST JSON to `POST /api/environment/ingest` (already implemented & tested).
2. Implement `RealIoTSensorService.read(location)` (sketch included in `sensor_service.py`) and switch the factory.
3. Optional: store raw readings in a time-series source behind `EnvironmentalData`.

Nothing else changes — alerts, SMS, priorities and the frontend keep working with real data.

## Future ML integration

1. Train a scikit-learn model (RandomForest / GradientBoosting) on historical samples + observed landslide outcomes.
2. Add `LearnedRiskEngine(BaseRiskEngine)` in `backend/app/ml/risk_engine.py` (annotated template included) wrapping the pickled pipeline.
3. Return it from `get_risk_engine()` — done. Interfaces (`RiskFeatures` → `RiskResult`) are stable; the UI and services never touch the model directly.

## Testing

Backend endpoints are verified with curl; the frontend ships **vitest + jsdom smoke tests** that boot every page against the live backend and run the full simulation workflow:

```bash
# backend running on :8000 (see above), then:
cd frontend
npm test          # 11 tests: 10 page renders + 1 full EXTREME_RAIN pipeline run
```

## FAQ

**Does it need IoT hardware / paid APIs?** No. Everything runs with simulated sensors, simulated SMS and free OpenStreetMap tiles.

**Does it predict when a landslide will happen?** No — it predicts current 24h risk/probability and classifies zones so authorities can act early.

**Where is data stored?** `backend/ner_landslideai.db` (SQLite), auto-created and deterministically seeded on first run. Delete the file and restart to reset the demo.

**Can the dashboard be shown on a projector?** Yes — it is responsive and readable at 1080p.

---

*NER LandslideAI — academic/government demonstration prototype for disaster management in the North Eastern Region of India.*
