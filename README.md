# EHAZOP Platform

A web-based software platform for digitizing Safety and Operability (SAFOP) and Electrical HAZOP (EHAZOP) studies for industrial facilities.

## Overview

The EHAZOP Platform replaces spreadsheet-and-meeting workflows with a collaborative web application that:
- Captures study nodes and applies guidewords to surface deviations
- Records causes, consequences, safeguards, and risk rankings
- Tracks recommendations to close-out
- Augments human workshops with AI assistance grounded in organizational knowledge

## Features

- **Authentication & RBAC** - JWT-based authentication with role-based access control (Admin, Facilitator, Scribe, Participant, Viewer)
- **Study Lifecycle Management** - Create and manage SAFOP/EHAZOP studies across SAFAN, SYSOP, OPTAN, and EHAZOP study types
- **HAZOP Node CRUD** - Define nodes with design intent, equipment type, and drawing references
- **Guideword-driven Deviation Worksheets** - Configurable guideword libraries for systematic deviation analysis
- **Risk Assessment Engine** - Configurable P/A/E/R risk matrix with severity (1-5) and likelihood (A-E) scales
- **LLM Assistance** - AI-powered suggestions for causes, consequences, and safeguards using Google Gemini
- **RAG Knowledge Base** - Vector-based retrieval of past HAZOPs and P&IDs for grounding AI suggestions
- **Report Generation** - PDF (WeasyPrint) and Excel (openpyxl) study reports
- **Real-time Collaboration** - WebSocket-based live worksheet updates and row locking
- **Action Tracking** - Full lifecycle recommendation tracking with carry-forward between studies

## Tech Stack

**Backend:**
- Python 3.14+
- FastAPI 0.136.x
- SQLAlchemy 2.0 (async)
- PostgreSQL + pgvector
- Pydantic v2
- JWT + bcrypt authentication
- Google Gemini for LLM

**Frontend:**
- React 19
- TypeScript
- Vite
- Ant Design v6
- TanStack Query
- Zustand

## Project Structure

```
ehazop_backend/
├── app/
│   ├── main.py           # FastAPI entry point
│   ├── core/             # Configuration, database, security
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic validation schemas
│   ├── services/         # Business logic
│   └── routes/           # API endpoints
├── alembic/              # Database migrations
├── scripts/             # Utility scripts
├── requirements.txt
├── Dockerfile
└── .env

frontend/
├── src/
│   ├── api/              # API client
│   ├── features/        # React components
│   ├── store/           # Zustand stores
│   └── theme/           # CSS/theme
├── package.json
└── vite.config.ts
```

## Quick Start

### Using Docker Compose

```bash
# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Seed demo data
docker-compose exec backend python scripts/seed_data.py
```

### Manual Setup

**Backend:**
```bash
cd ehazop_backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Set up environment
cp ../.env.example .env
# Edit .env with your settings

# Run database migrations
alembic upgrade head

# Seed demo data
python scripts/seed_data.py

# Start the server
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Configuration

Key environment variables (see `.env.example`):

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | JWT signing key (change in production!) |
| `DATABASE_URL` | PostgreSQL connection string |
| `GEMINI_API_KEY` | Google Gemini API key for LLM |
| `STORAGE_TYPE` | Storage backend: `local`, `s3`, or `minio` |

## API Endpoints

The API is versioned under `/api/v1`:

| Group | Endpoints |
|-------|-----------|
| Auth | `/auth/login`, `/auth/refresh`, `/auth/register`, `/auth/me` |
| Studies | `/studies`, `/studies/{id}`, `/studies/{id}/members` |
| Nodes | `/studies/{id}/nodes`, `/nodes/{id}` |
| Deviations | `/deviations`, `/deviations/{id}/causes`, `/consequences`, `/safeguards` |
| Risk | `/risk-matrices`, `/risk-matrices/calculate` |
| LLM | `/llm/suggest/{deviation_id}` |
| Knowledge | `/knowledge/search`, `/knowledge/ingest` |
| Actions | `/actions`, `/actions/{id}/verify` |
| Reports | `/reports/generate/{study_id}/pdf`, `/reports/generate/{study_id}/excel` |

## Demo Accounts

After seeding the database:

| Email | Password | Role |
|-------|----------|------|
| admin@ehazop.local | admin123 | Administrator |
| facilitator@ehazop.local | facilitator123 | Facilitator |
| scribe@ehazop.local | scribe123 | Scribe |
| participant@ehazop.local | participant123 | Participant |

## Development

### Running Tests
```bash
# Backend
cd ehazop_backend
pytest

# Frontend
cd frontend
npm run test
```

### Code Quality
```bash
# Backend linting
cd ehazop_backend
ruff check .
black .

# Frontend linting
cd frontend
npm run lint
```

## License

Proprietary - All rights reserved