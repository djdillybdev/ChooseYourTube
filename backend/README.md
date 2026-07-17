# ChooseYourTube API

This directory contains the FastAPI API, database models, services, and arq worker. The root
[README](../README.md) covers the product and Docker installation; this guide is for backend
development.

## Responsibilities

The backend owns:

- accounts and owner-scoped channels, videos, categories, tags, and playlists;
- Watch Later, ordered playlist membership, and watched state;
- Google Takeout CSV and one-time Google OAuth subscription imports;
- durable synchronization records, retries, and YouTube API quota accounting;
- RSS-first channel refresh with optional Data API metadata;
- Redis-backed jobs, worker health, and hourly scheduling in full mode;
- shared-demo login and daily RSS-only maintenance in demo mode.

## Project structure

```text
app/
  auth/        Authentication and rotating sessions
  clients/     YouTube RSS and Data API clients
  core/        Settings, errors, and observability
  db/          SQLAlchemy models, sessions, and owner-scoped CRUD
  routers/     HTTP request and response handling
  schemas/     Pydantic API contracts
  services/    Application orchestration
  main.py      FastAPI entry point
  worker.py    arq worker and hourly scheduler
migration/     Alembic configuration and revisions
scripts/       OpenAPI, migration, coverage, and demo utilities
tests/         Unit, CRUD, service, router, worker, and integration tests
```

Routers validate HTTP input and delegate work to services. Services coordinate external clients and
CRUD modules. Database and network boundaries are asynchronous.

## Requirements

- Python 3.12
- `uv`
- PostgreSQL 16
- Redis 7 for full-mode background work

The root Compose stack is the shortest way to start PostgreSQL and Redis. From the repository root:

```bash
cp .env.example .env
# Set YOUTUBE_API_KEY and replace AUTH_SECRET.
docker compose --env-file .env up -d postgres redis

cd backend
uv sync --frozen
uv run --env-file ../.env alembic upgrade head
uv run --env-file ../.env uvicorn app.main:app --reload
```

Run the worker in a second terminal:

```bash
cd backend
uv run --env-file ../.env arq app.worker.WorkerSettings
```

The API documentation is available at <http://localhost:8000/docs>. Liveness and dependency checks
are exposed at `/health/live` and `/health/ready`.

## Runtime modes

`APP_MODE=full` enables registration, imports, channel changes, Redis jobs, scheduled refresh, and
quota-accounted Data API work. Full mode requires PostgreSQL, Redis, a YouTube API key, and a stable
authentication secret.

`APP_MODE=demo` supports the restricted Vercel deployment through `app.index:app`. It uses the same
routers, services, models, and migrations, but backend policy disables registration, external imports,
channel mutation, and API-key-dependent refreshes.

Google OAuth is optional in full mode. For the default Docker stack, the registered callback is
`http://localhost:8000/imports/youtube/oauth/callback`. Credentials are used for subscription
discovery and are not stored.

See the root [configuration overview](../README.md#configuration) and the complete
[deployment reference](../docs/deployment.md#configuration-reference).

## API contract

The checked-in OpenAPI document generates the frontend TypeScript types. After changing a router or
schema, run from this directory:

```bash
cd ../frontend
pnpm api:generate
pnpm api:check
```

Public errors use this shape:

```json
{
  "code": "ERROR_CODE",
  "message": "Safe user-facing message.",
  "request_id": "correlation-id",
  "retryable": false
}
```

Public error bodies must not contain connection strings, credentials, SQL, stack traces, or upstream
response bodies.

## Database migrations

```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "describe change"
uv run alembic check
```

Review every generated revision before committing it. Production migrations use a direct PostgreSQL
connection and run before application code that depends on the new schema. See the
[migration guide](migration/README) and [deployment guide](../docs/deployment.md#upgrades-and-rollback)
for operational details.

## Validation

```bash
uv run ruff check app tests scripts
uv run mypy app
uv run pytest
uv run python scripts/check_coverage.py
uv run alembic check
```

Pytest measures line and branch coverage. The release gate requires at least 80% backend coverage.
Authentication, ownership, imports, quota accounting, and worker behavior still require direct tests
when aggregate coverage passes.
