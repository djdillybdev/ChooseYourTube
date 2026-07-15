from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.pool import NullPool

from app.db import session
from app.index import app


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
