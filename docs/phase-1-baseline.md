# Phase 1 baseline

Baseline captured on 2026-07-14 before and during Phase 1 implementation.

## Initial state

- `docker compose --env-file .env.example config --quiet`: passed.
- Backend and frontend checks initially could not run because dependencies were not installed and sandboxed network access was unavailable.
- After installing locked dependencies, Ruff exposed six pre-existing unused imports; these were removed.
- The frontend formatter reported existing formatting drift across the project.
- Once mypy package discovery was corrected, it exposed a pre-existing backlog of 139 type errors concentrated in generic CRUD/service return types. This is recorded rather than hidden with ignores.

## Phase 1 verification

Final results after the Phase 1 stabilization pass:

- Backend Ruff: passed across the application, tests, and migrations.
- Backend mypy: passed with no issues in 49 source files.
- Backend pytest: **672 passed**, 86.99% total coverage.
- Frontend OpenAPI drift check: passed.
- Frontend Svelte/TypeScript check: passed with zero diagnostics.
- Frontend Prettier and ESLint: passed.
- Frontend unit/component coverage: **83 tests passed**; 83.05% statements, 79.82% branches, 71.69% functions, and 86.24% lines.
- Frontend Playwright: **1 test passed**.
- Compose configuration and production image builds: passed.
- Full Compose startup: passed. PostgreSQL, Redis, backend, worker, and frontend started; the one-shot migration container exited successfully.
- Operational smoke checks: `/health/live`, `/health/ready`, `/`, and the frontend `/api/meta` proxy all returned successful responses. Full-mode readiness reported database, migrations, Redis, and worker heartbeat as healthy.

The Compose pass found and fixed one configuration regression: `.env.example` intentionally leaves `DEMO_USER_EMAIL` blank in full mode, so blank optional email values are now normalized to unset before email validation.

Commands used:

```bash
cd backend
UV_CACHE_DIR=/tmp/chooseyourtube-uv-cache uv run ruff check .
uv run mypy app
uv run pytest

cd ../frontend
pnpm api:check
pnpm check
pnpm lint
pnpm test:coverage
pnpm test:e2e

cd ..
docker compose --env-file .env.example config --quiet
docker compose --env-file .env.example up -d --build
docker compose --env-file .env.example ps -a
curl --fail http://localhost:8000/health/live
curl --fail http://localhost:8000/health/ready
curl --fail http://localhost:8000/
curl --fail http://localhost:5173/api/meta
```
