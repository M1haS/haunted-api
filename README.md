# 👻 Haunted API

A REST API for cataloging, classifying and analyzing paranormal events and haunted locations.

## Features

- 📍 **Location registry** — store haunted places with coordinates and threat level
- 👁️ **Event tracking** — log paranormal incidents with witnesses and evidence type
- 🔬 **Classification engine** — auto-classify events (poltergeist / apparition / infrasound / unknown)
- 📊 **Statistics & heatmap data** — hotspot detection, activity trends by moon phase
- 🔒 **Investigator auth** — JWT-based roles (field_agent / analyst / admin)

## Tech Stack

- **FastAPI** — async REST framework
- **SQLAlchemy** (async) — ORM with SQLite (swappable to Postgres)
- **Pydantic v2** — request/response validation
- **SlowAPI** — rate limiting per investigator
- **Uvicorn** — ASGI server

## Quick Start

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Project Structure

```
haunted-api/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── config.py
│   ├── routers/
│   │   ├── locations.py
│   │   ├── events.py
│   │   ├── investigators.py
│   │   └── stats.py
│   ├── models/
│   │   └── models.py
│   ├── schemas/
│   │   └── schemas.py
│   └── services/
│       ├── classifier.py
│       └── heatmap.py
└── tests/
    └── test_events.py
```

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/locations` | List all haunted locations |
| POST | `/locations` | Register new location |
| GET | `/locations/{id}/events` | Events at a location |
| POST | `/events` | Log paranormal event |
| GET | `/events/{id}/classify` | Auto-classify event |
| GET | `/stats/hotspots` | Top activity hotspots |
| GET | `/stats/moon-phase` | Activity by lunar phase |

## Classification Logic

Events are scored across 4 axes:
- **Kinetic** (object movement, sounds)
- **Visual** (apparitions, shadows, orbs)
- **Thermal** (cold spots, heat anomalies)
- **Electronic** (EMF spikes, device interference)

Score threshold → assigned class → threat level (1–5 ☠️)

---

> *"The oldest and strongest emotion of mankind is fear, and the oldest and strongest kind of fear is fear of the unknown."* — H.P. Lovecraft
