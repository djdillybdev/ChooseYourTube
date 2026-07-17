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
    assert response.json()["service"]["version"] == "1.0.0"


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

    paths = {route.path for route in demo_app.routes}
    assert "/auth/register" not in paths
    assert "/auth/jwt/login" not in paths
    assert "/auth/demo" in paths


def test_incomplete_email_flows_are_not_exposed() -> None:
    paths = {route.path for route in app.routes}
    assert "/auth/forgot-password" not in paths
    assert "/auth/reset-password" not in paths
    assert "/auth/request-verify-token" not in paths
    assert "/auth/verify" not in paths


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


@pytest.mark.asyncio
async def test_readiness_reports_database_and_migration_failures(monkeypatch) -> None:
    unavailable = AsyncMock()
    unavailable.execute.side_effect = RuntimeError("database offline")
    response = await health.readiness(unavailable)
    assert response.status_code == 503
    assert b'"database":{"status":"unavailable","required":true}' in response.body

    migration_failure = AsyncMock()
    migration_failure.execute.side_effect = [MagicMock(), RuntimeError("no version table")]
    monkeypatch.setattr(health.settings, "BACKGROUND_JOBS_ENABLED", False)
    response = await health.readiness(migration_failure)
    assert response.status_code == 503
    assert b'"migrations":{"status":"incompatible","required":true}' in response.body


@pytest.mark.asyncio
async def test_full_mode_readiness_requires_redis_and_worker(monkeypatch) -> None:
    session = AsyncMock()
    migration_result = MagicMock()
    migration_result.fetchall.return_value = [("head-revision",)]
    session.execute.side_effect = [MagicMock(), migration_result]
    monkeypatch.setattr(health, "_migration_heads", lambda: {"head-revision"})
    monkeypatch.setattr(health.settings, "BACKGROUND_JOBS_ENABLED", True)

    redis = AsyncMock()
    redis.get.return_value = b'{"worker":"worker-1"}'
    monkeypatch.setattr(health.arq, "create_pool", AsyncMock(return_value=redis))
    response = await health.readiness(session)
    assert response.status_code == 200
    assert b'"worker":{"status":"ok","required":true}' in response.body
    redis.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_full_mode_readiness_rejects_missing_worker_and_redis_failure(
    monkeypatch,
) -> None:
    monkeypatch.setattr(health.settings, "BACKGROUND_JOBS_ENABLED", True)
    redis = AsyncMock()
    redis.get.return_value = None
    monkeypatch.setattr(health.arq, "create_pool", AsyncMock(return_value=redis))
    checks, ready = await health._background_checks()
    assert ready is False
    assert checks["worker"]["status"] == "stale_or_missing"

    monkeypatch.setattr(
        health.arq, "create_pool", AsyncMock(side_effect=ConnectionError("redis offline"))
    )
    checks, ready = await health._background_checks()
    assert ready is False
    assert checks["redis"]["status"] == "unavailable"
