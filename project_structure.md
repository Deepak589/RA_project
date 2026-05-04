# Project Structure

## Backend

- `app/` - FastAPI application package for API, business logic, and persistence.
- `app/core/` - Runtime configuration, security helpers, and framework-wide settings.
- `app/db/` - SQLAlchemy base metadata, async sessions, and database integration.
- `app/models/` - ORM models and shared database enums.
- `app/schemas/` - Pydantic request and response contracts.
- `app/routers/` - API route modules grouped by domain.
- `app/services/` - Recommendation, ingestion, and orchestration services.
- `alembic/` - Migration environment and reusable Alembic configuration.
- `alembic/versions/` - Database revision files, starting with the initial schema.
- `database/` - Raw SQL artifacts and the Mermaid ER diagram.
- `tests/` - Test suite root for backend verification.
- `tests/models/` - ORM and persistence-focused tests.
- `tests/schemas/` - Contract validation tests for Pydantic schemas.
- `tests/services/` - Service-layer behavior tests.

## Frontend

- `frontend/` - React + Vite application root.
- `frontend/public/` - Static assets copied directly into the built frontend bundle.
- `frontend/src/` - Frontend source package for UI, state, and API access.
- `frontend/src/api/` - HTTP clients and API adapters for backend endpoints.
- `frontend/src/components/` - Reusable presentational and layout components.
- `frontend/src/hooks/` - Shared React hooks for async state and UI flows.
- `frontend/src/pages/` - Route-level screens that map to Week 1 UI inventory.
- `frontend/src/store/` - App-level state management modules.
- `frontend/src/utils/` - Pure helpers for formatting, validation, and view logic.

## Root Files

- `.env.example` - Backend environment variable template for local development.
- `requirements.txt` - Python dependency manifest for FastAPI, SQLAlchemy, and Alembic.
- `Dockerfile` - Backend container build recipe.
- `docker-compose.yml` - Local multi-service dev stack for API and PostgreSQL.
- `week1_requirements.md` - Completed Week 1 product requirements baseline.
- `week2_summary.md` - Week 2 handoff summary for the next implementation phase.
