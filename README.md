# Real Estate Agent Tools

A platform for independent real estate agents and small brokerages that streamlines day-to-day workflows and adds data intelligence that larger platforms don't provide. Built for the Indiana/Kentucky market.

## What It Does

- **Property management** — add and manage listings and buyer-side representations with full parcel data, county boundaries, and map overlays
- **AI property chat** — ask questions about a property using uploaded documents and property details as context
- **Net sheet** — seller net proceeds calculator with real property tax proration (Indiana DLGF integration)
- **Document management** — upload, view, and delete property documents
- **Crime heatmap** — raster tile overlay for violent and property crime (Louisville metro)
- **Social post generation** — AI-generated listing copy from property details and documents; multi-platform posting support in progress
- **Multi-tenant auth** — brokerage and agent accounts with JWT authentication

See [docs/ROADMAP.md](docs/ROADMAP.md) for what's planned next.

---

## Tech Stack

**Backend**
- Python 3.11, FastAPI, SQLModel (SQLite)
- `poetry` for package management
- OpenAI API (chat and embeddings)
- Milvus (document vector search)
- AWS S3 (document storage)
- ArcGIS IGIS (parcel data)
- Indiana DLGF (property tax data)

**Frontend**
- React 18, Tailwind CSS
- Mapbox GL / react-map-gl
- React Router

**Pipeline**
- Separate Python/Prefect service for data ingestion (crime heatmap, property tax)

---

## Running Locally

### Prerequisites

- Python 3.11+
- Node 18+
- `poetry` (`pip install poetry`)
- Docker and Docker Compose (for Milvus)

### 1. Start supporting services

```bash
docker-compose up -d
```

This starts Milvus (vector database) and its dependencies (etcd, MinIO).

### 2. Backend

```bash
cd backend
cp .env.example .env   # fill in your API keys
poetry install
poetry run uvicorn backend.main:app --reload
```

The backend runs on `http://localhost:3000`.

Required environment variables (see `.env.example` for full list):

```
OPENAI_API_KEY=
RENTCAST_API_KEY=
GOOGLE_MAPS_API_KEY=
MILVUS_URI=http://localhost:19530
S3_BUCKET=
S3_ACCESS_KEY=
S3_SECRET_KEY=
JWT_SECRET_KEY=
```

### 3. Frontend

```bash
cd frontend
npm install
npm start
```

The frontend runs on `http://localhost:3001` and expects the backend at `http://localhost:3000`.

### 4. Pipeline (optional)

The pipeline ingests crime and property tax data. Only needed if you are working on data pipeline features.

```bash
cd pipeline
poetry install
poetry run python -m pipeline.flows.<flow_name>
```

---

## Running Tests

```bash
# Backend
cd backend && poetry run pytest

# Frontend
cd frontend && npm test

# Pipeline
cd pipeline && poetry run pytest
```

---

## Project Structure

```
backend/        FastAPI backend, SQLModel models, services, repositories
frontend/       React frontend
pipeline/       Data ingestion pipeline (crime heatmap, property tax)
docs/           Product documentation and roadmap
```

---

## Database

The database is a SQLite file at `backend/real_estate.db`. It is created automatically on first run.

Schema migrations are currently handled by a temporary script while the schema foundation is being established. This will be replaced with Alembic once the schema stabilises.

```bash
cd backend

# Apply schema changes (temporary — will be replaced by Alembic)
poetry run python scripts/migrate_db.py

# Migrate data from legacy schema (one-time, if upgrading from an older version)
poetry run python scripts/migrate_property_info.py
```
