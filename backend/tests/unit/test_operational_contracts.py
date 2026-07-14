from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import Settings
from app.main import app, create_app
from app.routers import health


def test_root_exposes_public_metadata() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json()["name"] == "ChooseYourTube API"
    assert response.json()["links"]["readiness"] == "/health/ready"
    assert "X-Request-ID" in response.headers


def test_liveness_is_cheap_and_identified() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"]["version"] == "0.1.0"


def test_unknown_route_uses_safe_error_contract() -> None:
    with TestClient(app) as client:
        response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "code": "NOT_FOUND",
        "message": "The requested resource was not found.",
        "request_id": response.headers["X-Request-ID"],
        "retryable": False,
    }


def test_registration_router_is_omitted_when_disabled() -> None:
    configured = Settings(
        APP_ENV="test",
        APP_MODE="demo",
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        BACKGROUND_JOBS_ENABLED=False,
        YOUTUBE_API_KEY=None,
        DEMO_USER_EMAIL="demo@example.com",
        DEMO_MAINTENANCE_SECRET="d" * 32,
    )
    demo_app = create_app(configured)

    assert "/auth/register" not in {route.path for route in demo_app.routes}


@pytest.mark.asyncio
async def test_demo_readiness_does_not_require_background_services(monkeypatch) -> None:
    session = AsyncMock()
    migration_result = MagicMock()
    migration_result.fetchall.return_value = [("head-revision",)]
    session.execute.side_effect = [MagicMock(), migration_result]
    monkeypatch.setattr(health, "_migration_heads", lambda: {"head-revision"})
    monkeypatch.setattr(health.settings, "BACKGROUND_JOBS_ENABLED", False)

    response = await health.readiness(session)

    assert response.status_code == 200
    assert b'"redis":{"status":"not_required","required":false}' in response.body


@pytest.mark.asyncio
async def test_migration_drift_makes_readiness_fail(monkeypatch) -> None:
    session = AsyncMock()
    migration_result = MagicMock()
    migration_result.fetchall.return_value = [("old-revision",)]
    session.execute.side_effect = [MagicMock(), migration_result]
    monkeypatch.setattr(health, "_migration_heads", lambda: {"head-revision"})
    monkeypatch.setattr(health.settings, "BACKGROUND_JOBS_ENABLED", False)

    response = await health.readiness(session)

    assert response.status_code == 503
    assert b'"migrations":{"status":"incompatible","required":true}' in response.body
