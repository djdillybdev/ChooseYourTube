from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from arq.connections import ArqRedis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApplicationError
from app.db.crud import crud_sync_run
from app.db.models.sync_run import SyncRun
from app.schemas.base import PaginatedResponse
from app.schemas.sync_run import (
    LatestSyncSummary,
    SyncRunKind,
    SyncRunOut,
    SyncRunStatus,
)

logger = logging.getLogger(__name__)

RETRYABLE_ERROR_CODES = {
    "RSS_FETCH_FAILED",
    "UPSTREAM_TIMEOUT",
    "YOUTUBE_RATE_LIMITED",
    "YOUTUBE_UPSTREAM_ERROR",
    "QUEUE_UNAVAILABLE",
}


@dataclass(slots=True)
class SyncProgress:
    discovered: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0

    def add(self, other: "SyncProgress") -> None:
        self.discovered += other.discovered
        self.created += other.created
        self.updated += other.updated
        self.skipped += other.skipped
        self.failed += other.failed


def is_retryable(run: SyncRun) -> bool:
    return run.error_code in RETRYABLE_ERROR_CODES


def to_sync_run_out(run: SyncRun) -> SyncRunOut:
    output = SyncRunOut.model_validate(run)
    return output.model_copy(update={"retryable": is_retryable(run)})


def to_latest_summary(
    run: SyncRun, last_successful_at: datetime | None
) -> LatestSyncSummary:
    return LatestSyncSummary(
        id=run.id,
        kind=SyncRunKind(run.kind),
        status=SyncRunStatus(run.status),
        error_code=run.error_code,
        error_message=run.error_message,
        retryable=is_retryable(run),
        queued_at=run.queued_at,
        finished_at=run.finished_at,
        last_successful_at=last_successful_at,
    )


async def create_or_get_active_run(
    db_session: AsyncSession,
    *,
    owner_id: str,
    kind: SyncRunKind,
    channel_id: str | None = None,
    subscription_import_id: uuid.UUID | None = None,
    max_attempts: int = 4,
) -> tuple[SyncRun, bool]:
    if channel_id is not None or subscription_import_id is not None:
        existing = await crud_sync_run.get_active_sync_run(
            db_session,
            owner_id=owner_id,
            channel_id=channel_id,
            subscription_import_id=subscription_import_id,
            kind=kind.value,
        )
        if existing is not None:
            return existing, False

    run = SyncRun(
        owner_id=owner_id,
        kind=kind.value,
        status=SyncRunStatus.QUEUED.value,
        channel_id=channel_id,
        subscription_import_id=subscription_import_id,
        max_attempts=max_attempts,
    )
    db_session.add(run)
    try:
        await db_session.commit()
    except IntegrityError:
        await db_session.rollback()
        if channel_id is None and subscription_import_id is None:
            raise
        existing = await crud_sync_run.get_active_sync_run(
            db_session,
            owner_id=owner_id,
            channel_id=channel_id,
            subscription_import_id=subscription_import_id,
            kind=kind.value,
        )
        if existing is None:
            raise
        return existing, False
    await db_session.refresh(run)
    return run, True


async def enqueue_run(
    db_session: AsyncSession,
    redis: ArqRedis,
    *,
    owner_id: str,
    kind: SyncRunKind,
    channel_id: str | None = None,
    subscription_import_id: uuid.UUID | None = None,
    defer_seconds: int = 0,
) -> SyncRun:
    run, created = await create_or_get_active_run(
        db_session,
        owner_id=owner_id,
        kind=kind,
        channel_id=channel_id,
        subscription_import_id=subscription_import_id,
    )
    if not created:
        return run

    try:
        if defer_seconds:
            await redis.enqueue_job(
                "execute_sync_run",
                str(run.id),
                _job_id=str(run.id),
                _defer_by=defer_seconds,
            )
        else:
            await redis.enqueue_job(
                "execute_sync_run", str(run.id), _job_id=str(run.id)
            )
    except Exception as exc:
        run.status = SyncRunStatus.FAILED.value
        run.error_code = "QUEUE_UNAVAILABLE"
        run.error_message = "The synchronization queue is temporarily unavailable."
        run.finished_at = datetime.now(timezone.utc)
        await db_session.commit()
        logger.exception(
            "sync_enqueue_failed",
            extra={
                "sync_run_id": str(run.id),
                "task_kind": run.kind,
                "owner_id": owner_id,
                "channel_id": channel_id,
                "outcome": "failed",
            },
        )
        raise ApplicationError(
            "QUEUE_UNAVAILABLE",
            "Synchronization is temporarily unavailable.",
            status_code=503,
            retryable=True,
        ) from exc
    return run


async def list_runs(
    db_session: AsyncSession,
    *,
    owner_id: str,
    status: SyncRunStatus | None,
    kind: SyncRunKind | None,
    channel_id: str | None,
    limit: int,
    offset: int,
) -> PaginatedResponse[SyncRunOut]:
    runs, total = await crud_sync_run.list_sync_runs(
        db_session,
        owner_id=owner_id,
        status=status.value if status else None,
        kind=kind.value if kind else None,
        channel_id=channel_id,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse[SyncRunOut](
        total=total,
        items=[to_sync_run_out(run) for run in runs],
        limit=limit,
        offset=offset,
        has_more=offset + len(runs) < total,
    )


async def get_owned_run(
    db_session: AsyncSession, sync_run_id: uuid.UUID, owner_id: str
) -> SyncRun:
    run = await crud_sync_run.get_sync_run(
        db_session, sync_run_id, owner_id=owner_id
    )
    if run is None:
        raise ApplicationError("NOT_FOUND", "Synchronization run not found.", 404)
    return run


async def retry_run(
    db_session: AsyncSession,
    redis: ArqRedis,
    *,
    sync_run_id: uuid.UUID,
    owner_id: str,
) -> SyncRun:
    previous = await get_owned_run(db_session, sync_run_id, owner_id)
    if previous.status not in {"partial", "failed"} or not is_retryable(previous):
        raise ApplicationError(
            "SYNC_NOT_RETRYABLE", "This synchronization cannot be retried.", 409
        )
    return await enqueue_run(
        db_session,
        redis,
        owner_id=owner_id,
        kind=SyncRunKind(previous.kind),
        channel_id=previous.channel_id,
        subscription_import_id=previous.subscription_import_id,
    )
