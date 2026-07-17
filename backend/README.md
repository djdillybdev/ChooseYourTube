# ChooseYourTube API

FastAPI backend for the ChooseYourTube distraction-free YouTube inbox. The root [README](../README.md)
is the primary product and setup guide; this document covers backend development.

## Responsibilities

- Owner-scoped accounts, channels, videos, categories, tags and playlists.
- Watch Later and ordered playback state.
- Google Takeout CSV and one-time Google OAuth subscription imports.
- Durable synchronization runs, quota accounting and safe retry/failure contracts.
- RSS-first refresh with optional YouTube Data API enrichment.
- Full-mode Redis/arq scheduling and worker health.
- Restricted demo login and RSS-only daily maintenance.

## Structure

```text
app/
  auth/        Authentication and rotating sessions
  clients/     YouTube RSS/Data API boundaries
  core/        Settings, errors and observability
  db/          Models, sessions and owner-scoped CRUD
  routers/     HTTP request/response handlers
  schemas/     Pydantic contracts
  services/    Business orchestration
  main.py      FastAPI entrypoint
  worker.py    arq worker and hourly scheduler
migration/     Alembic configuration and revisions
scripts/       OpenAPI, demo seed and migration checks
tests/         Unit, CRUD, service, router, worker and integration tests
```

Routers stay thin, services own orchestration, CRUD modules own queries and all database/network
boundaries remain explicitly asynchronous.

## Local development

Requirements: Python 3.12, `uv`, PostgreSQL 16 and Redis 7. The root Compose stack is the simplest way
to start infrastructure. Run these commands from the repository root:

```bash
cp .env.example .env
docker compose --env-file .env up -d postgres redis

cd backend
uv sync --frozen
uv run --env-file ../.env alembic upgrade head
uv run --env-file ../.env uvicorn app.main:app --reload
```

Run the full-mode worker in another terminal:

```bash
cd backend
uv run --env-file ../.env arq app.worker.WorkerSettings
```

API documentation is available at <http://localhost:8000/docs>. Process and dependency checks are
available at `/health/live` and `/health/ready`.

The hosted demo uses `app.index:app` as its Vercel entrypoint. It shares routers, services, models and
migrations with the full application but disables Redis-backed jobs, public registration and
quota-sensitive mutations through validated runtime settings.

## Configuration

Settings are validated in `app/core/config.py`. Full mode requires PostgreSQL, Redis, a YouTube API key
and a stable auth secret. Demo mode requires PostgreSQL, a demo account email and a 32+ character cron
secret, but deliberately rejects background/API-key-dependent operations.

Google OAuth is optional. When enabled, configure a web client whose redirect URI exactly matches
`http://localhost:8000/imports/youtube/oauth/callback` for the default local stack. Credentials are
used only for discovery and are not persisted.

See the root [configuration table](../README.md#configuration) and [deployment guide](../docs/deployment.md)
for the complete environment contract.

## API contract

OpenAPI is the source of truth for the frontend. After changing a router or schema:

```bash
cd ../frontend
pnpm run api:generate
pnpm run api:check
```

Public errors use a stable body:

```json
{
  "code": "ERROR_CODE",
  "message": "Safe user-facing message.",
  "request_id": "correlation-id",
  "retryable": false
}
```

Do not expose connection strings, tokens, SQL, stack traces or upstream response bodies.

## Validation

```bash
uv run ruff check app tests scripts
uv run mypy app
uv run pytest
uv run python scripts/check_coverage.py
uv run alembic check
```

Pytest includes line and branch coverage. Auth, ownership, imports, quota accounting and workers require
direct tests even when aggregate coverage passes. The release gate requires at least 80% backend
coverage.

## Migrations and operations

```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "describe change"
```

Review generated revisions before committing them. Production migrations use a direct PostgreSQL URL
and run before code that requires the new schema. Runtime request traffic may use a pooled URL.

Backup, restore, release images and rollback are covered in [Deployment](../docs/deployment.md).
