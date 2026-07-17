"""Liveness and dependency-readiness endpoints."""

from __future__ import annotations

import logging
from pathlib import Path

import arq
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from ..core.config import settings
from ..core.version import APP_VERSION
from ..dependencies import DBSessionDep

router = APIRouter(prefix="/health", tags=["Health"])
logger = logging.getLogger(__name__)
WORKER_HEARTBEAT_KEY = "chooseyourtube:worker:heartbeat"


def _identity() -> dict[str, str]:
    return {
        "name": "ChooseYourTube API",
        "version": APP_VERSION,
        "mode": settings.APP_MODE,
    }


@router.get("/live", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK, include_in_schema=False)
async def liveness() -> dict[str, object]:
    return {"status": "ok", "service": _identity()}


def _migration_heads() -> set[str]:
    backend_root = Path(__file__).resolve().parents[2]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "migration"))
    return set(ScriptDirectory.from_config(config).get_heads())


async def _database_checks(db_session: DBSessionDep) -> tuple[dict[str, object], bool]:
    try:
        await db_session.execute(text("SELECT 1"))
    except Exception:
        logger.exception("readiness_database_failed")
        return {"database": {"status": "unavailable", "required": True}}, False

    try:
        result = await db_session.execute(text("SELECT version_num FROM alembic_version"))
        current = {str(row[0]) for row in result.fetchall()}
        compatible = current == _migration_heads()
    except Exception:
        logger.exception("readiness_migration_check_failed")
        compatible = False

    return (
        {
            "database": {"status": "ok", "required": True},
            "migrations": {
                "status": "ok" if compatible else "incompatible",
                "required": True,
            },
        },
        compatible,
    )


async def _background_checks() -> tuple[dict[str, object], bool]:
    if not settings.BACKGROUND_JOBS_ENABLED:
        return (
            {
                "redis": {"status": "not_required", "required": False},
                "worker": {"status": "not_required", "required": False},
            },
            True,
        )

    redis = None
    try:
        redis = await arq.create_pool(settings.get_redis_settings())
        await redis.ping()
        heartbeat = await redis.get(WORKER_HEARTBEAT_KEY)
        worker_ok = heartbeat is not None
        return (
            {
                "redis": {"status": "ok", "required": True},
                "worker": {
                    "status": "ok" if worker_ok else "stale_or_missing",
                    "required": True,
                },
            },
            worker_ok,
        )
    except Exception:
        logger.exception("readiness_background_check_failed")
        return (
            {
                "redis": {"status": "unavailable", "required": True},
                "worker": {"status": "unknown", "required": True},
            },
            False,
        )
    finally:
        if redis is not None:
            await redis.close()


@router.get("/ready")
async def readiness(db_session: DBSessionDep) -> JSONResponse:
    database_checks, database_ok = await _database_checks(db_session)
    background_checks, background_ok = await _background_checks()
    ready = database_ok and background_ok
    return JSONResponse(
        status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "ready" if ready else "not_ready",
            "service": _identity(),
            "checks": {**database_checks, **background_checks},
        },
    )
