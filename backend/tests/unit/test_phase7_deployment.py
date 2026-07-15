from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy.pool import NullPool

from app.db import session
from app.index import app


def _production_demo_environment(database_url: str) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "production",
            "APP_MODE": "demo",
            "DATABASE_URL": database_url,
            "AUTH_SECRET": "migration-only-secret-not-used-by-runtime-2026",
            "DEMO_USER_EMAIL": "migration@example.com",
            "DEMO_MAINTENANCE_SECRET": "migration-only-maintenance-secret-2026",
            "ENABLE_STARTUP_SCHEMA_CHECK": "false",
        }
    )
    return env


def test_vercel_entrypoint_exports_fastapi_application() -> None:
    assert app.title == "ChooseYourTube API"


def test_serverless_database_mode_uses_no_process_local_pool(monkeypatch) -> None:
    monkeypatch.setattr(session.settings, "DATABASE_POOL_MODE", "serverless")

    assert session.engine_kwargs_for_runtime()["poolclass"] is NullPool


def test_persistent_database_mode_checks_and_recycles_connections(monkeypatch) -> None:
    monkeypatch.setattr(session.settings, "DATABASE_POOL_MODE", "persistent")

    kwargs = session.engine_kwargs_for_runtime()
    assert kwargs["pool_pre_ping"] is True
    assert kwargs["pool_recycle"] == 300
    assert "poolclass" not in kwargs


def test_vercel_configuration_has_daily_maintenance() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    configured = json.loads((backend_root / "vercel.json").read_text())

    assert configured["regions"] == ["fra1"]
    assert "functions" not in configured
    assert configured["crons"] == [
        {"path": "/internal/demo/maintenance", "schedule": "0 4 * * *"}
    ]


def test_migration_model_import_accepts_sync_database_url() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    sync_database_url = "postgresql+psycopg2://user:pass@localhost/database"
    env = _production_demo_environment(sync_database_url)
    env["ALEMBIC_DATABASE_URL"] = sync_database_url

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from app.db.models import User; assert User.__tablename__ == 'users'",
        ],
        cwd=backend_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_vercel_entrypoint_import_accepts_async_runtime_database_url() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    env = _production_demo_environment(
        "postgresql+asyncpg://user:pass@localhost/database?ssl=require"
    )

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from app.index import app; assert app.title == 'ChooseYourTube API'",
        ],
        cwd=backend_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_vercel_entrypoint_import_rejects_sync_runtime_url_safely() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    env = _production_demo_environment(
        "postgresql://user:super-secret@localhost/database"
    )

    result = subprocess.run(
        [sys.executable, "-c", "from app.index import app"],
        cwd=backend_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "use postgresql+asyncpg:// for PostgreSQL" in result.stderr
    assert "super-secret" not in result.stderr


def test_migration_workflow_uses_supported_head_verifier() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    workflow = (
        repository_root / ".github" / "workflows" / "production-migrate.yml"
    ).read_text()

    assert "python scripts/verify_migration_head.py" in workflow
    assert "--check-heads" not in workflow
