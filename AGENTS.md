# Repository Guidelines

## Project Structure & Module Organization

ChooseYourTube is a SvelteKit/FastAPI monorepo. `frontend/src/routes/` contains pages and server endpoints; shared UI, API clients, stores, and utilities live in `frontend/src/lib/`. Frontend tests are split across `frontend/tests/{unit,component,e2e}/`. Backend code lives in `backend/app/`: keep HTTP handlers in `routers/`, orchestration in `services/`, persistence in `db/crud/`, models in `db/models/`, and contracts in `schemas/`. Backend tests mirror these layers in `backend/tests/`; Alembic revisions live in `backend/migration/versions/`. See `backend/AGENTS.md` for more detail.

## Build, Test, and Development Commands

- `cp .env.example .env`: create local configuration; fill in required secrets.
- `make up`: build and start the stack at ports 5173 and 8000.
- `make dev-up`: start bind-mounted development services (frontend on 5174, API on 8001).
- `make logs` / `make down`: follow service logs or stop the stack.
- `make migrate`: apply Alembic migrations.
- `cd frontend && pnpm install && pnpm dev`: run the frontend directly.
- `cd frontend && pnpm check && pnpm lint && pnpm test:unit`: check and test frontend code.
- `cd frontend && pnpm test:e2e`: run Playwright browser tests.
- `cd backend && uv sync && uv run pytest`: install dependencies and run pytest with coverage.
- `cd backend && uv run ruff check . && uv run mypy app`: lint and type-check backend code.

## Coding Style & Naming Conventions

Prettier and ESLint enforce frontend formatting: tabs, single quotes, no trailing commas, and 100-column lines. Name Svelte components `PascalCase.svelte`; use `camelCase` for TypeScript values. Python targets 3.12+, uses four spaces, type hints, `snake_case` modules/functions, and `PascalCase` classes. Keep async database and network boundaries explicit.

## Testing Guidelines

Name Python tests `test_*.py` and frontend tests `*.test.ts` or `*.spec.ts`. Use pytest/pytest-asyncio and Hypothesis in the backend; use Vitest, Testing Library, and MSW in the frontend. Frontend coverage thresholds are 70%; backend coverage runs by default. Add regression tests for behavior changes.

## Commit & Pull Request Guidelines

History favors short, imperative subjects, sometimes with `feat:`, `fix:`, or `refactor:` prefixes. Keep commits focused. PRs should explain purpose and implementation, link issues, list commands run, and include screenshots for UI changes. Call out API, schema, migration, or configuration changes.

## Security & Configuration

Never commit `.env`, API keys, or auth secrets. Start from `.env.example`, use a strong `AUTH_SECRET`, and keep `YOUTUBE_API_KEY` local. Review migrations carefully and avoid destructive data changes without a documented rollback plan.
