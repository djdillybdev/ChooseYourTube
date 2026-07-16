from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Query, status

from app.core.config import settings
from app.core.errors import ApplicationError
from app.db.crud import crud_sync_run
from app.dependencies import ArqDep, CurrentUserDep, DBSessionDep
from app.schemas.base import PaginatedResponse
from app.schemas.sync_run import (
    SyncRunKind,
    SyncRunOut,
    SyncRunStatus,
    YouTubeQuotaStatusOut,
)
from app.services import sync_service

router = APIRouter(prefix="/sync-runs", tags=["Synchronization"])


def _require_background_jobs() -> None:
    if not settings.BACKGROUND_JOBS_ENABLED:
        raise ApplicationError(
            "FEATURE_DISABLED_IN_DEMO",
            "External refresh is disabled in the demo; data is maintained daily.",
            403,
        )


@router.get("", response_model=PaginatedResponse[SyncRunOut])
async def list_sync_runs(
    db_session: DBSessionDep,
    user: CurrentUserDep,
    status_filter: SyncRunStatus | None = Query(None, alias="status"),
    kind: SyncRunKind | None = Query(None),
    channel_id: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> PaginatedResponse[SyncRunOut]:
    return await sync_service.list_runs(
        db_session,
        owner_id=str(user.id),
        status=status_filter,
        kind=kind,
        channel_id=channel_id,
        limit=limit,
        offset=offset,
    )


@router.get("/quota", response_model=YouTubeQuotaStatusOut)
async def quota_status(
    db_session: DBSessionDep, user: CurrentUserDep
) -> YouTubeQuotaStatusOut:
    del user
    today = datetime.now(timezone.utc).date()
    units, calls = await crud_sync_run.quota_totals(db_session, today)
    budget = int(settings.YOUTUBE_DAILY_QUOTA_BUDGET or 0)
    return YouTubeQuotaStatusOut(
        date=today,
        budget=budget,
        estimated_units_used=units,
        estimated_units_remaining=max(0, budget - units),
        call_count=calls,
        exhausted=units >= budget,
    )


@router.get("/{sync_run_id}", response_model=SyncRunOut)
async def get_sync_run(
    sync_run_id: uuid.UUID, db_session: DBSessionDep, user: CurrentUserDep
) -> SyncRunOut:
    run = await sync_service.get_owned_run(db_session, sync_run_id, str(user.id))
    return sync_service.to_sync_run_out(run)


@router.post(
    "/{sync_run_id}/retry",
    response_model=SyncRunOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_sync_run(
    sync_run_id: uuid.UUID,
    db_session: DBSessionDep,
    redis: ArqDep,
    user: CurrentUserDep,
) -> SyncRunOut:
    _require_background_jobs()
    run = await sync_service.retry_run(
        db_session, redis, sync_run_id=sync_run_id, owner_id=str(user.id)
    )
    return sync_service.to_sync_run_out(run)
