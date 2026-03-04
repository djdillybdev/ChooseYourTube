# Repository Guidelines

## Project Structure & Module Organization
- `app/` contains runtime code.
- `app/main.py` boots the FastAPI API; `app/worker.py` defines arq worker settings.
- `app/routers/` holds HTTP endpoints, `app/services/` business logic, `app/db/crud/` data access, `app/db/models/` SQLAlchemy models, and `app/schemas/` Pydantic schemas.
- `app/auth/` contains authentication integration and user models; `app/clients/` contains external API clients.
- `migration/` contains Alembic env/config and versioned migrations.
- `tests/` is organized by scope (`unit/`, `integration/`, `routers/`, `services/`, `crud/`, `worker/`, etc.).

## Build, Test, and Development Commands
- `uv sync`: install dependencies from `pyproject.toml`/`uv.lock`.
- `docker compose up -d`: start PostgreSQL and Redis.
- `uv run alembic upgrade head`: apply DB migrations.
- `uv run uvicorn app.main:app --reload`: run API locally.
- `uv run arq app.worker.WorkerSettings`: run background worker.
- `uv run pytest`: run full test suite with coverage.
- `uv run pytest -m unit` / `uv run pytest -m integration`: run targeted subsets.
- `uv run ruff check` and `uv run mypy app`: lint and static type checks.

## Coding Style & Naming Conventions
- Target Python 3.12+, 4-space indentation, and type hints for public functions.
- Keep router handlers thin; place orchestration in services and persistence logic in CRUD modules.
- File/module names use `snake_case`; classes use `PascalCase`; tests follow `test_*.py`.
- Prefer small, focused functions and explicit async boundaries for DB/network operations.

## Testing Guidelines
- Framework: `pytest` with `pytest-asyncio`; property tests use Hypothesis.
- Mark tests with existing markers (`unit`, `integration`, `youtube_api`) as appropriate.
- Coverage is enabled by default (`--cov=app`); maintain or improve coverage on touched code.
- Add tests alongside behavior changes, especially for routers/services and migration-sensitive logic.

## Commit & Pull Request Guidelines
- Follow concise, imperative commit subjects; existing history often uses Conventional Commit prefixes (for example, `feat:`, `refactor:`).
- Keep commits scoped to one logical change and include tests/docs when relevant.
- PRs should include: purpose summary, key implementation notes, test evidence (commands run), and linked issues.
- For API or schema changes, include migration notes and sample request/response payloads when helpful.

## Security & Configuration Tips
- Copy `.env.example` to `.env`; never commit secrets.
- Required local variables include `DATABASE_URL`, `REDIS_URL`, `YOUTUBE_API_KEY`, and `AUTH_SECRET`.
- Use a strong `AUTH_SECRET` outside local development.
