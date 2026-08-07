from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import logging
import socket
import time
import uuid
import math
from datetime import datetime, timedelta, timezone

import arq
from arq import cron

from .clients.youtube import YouTubeAPI
from .core.config import settings
from .core.errors import ApplicationError
from .core.version import APP_VERSION
from .core.worker import WORKER_HEARTBEAT_KEY
from .db.crud import crud_sync_run
from .db.models.user_state import UserChannel
from .db.models.subscription_import import SubscriptionImport
from .db.models.sync_run import SyncRun
from sqlalchemy import select
from .db.session import sessionmanager
from .schemas.sync_run import SyncRunKind, SyncRunStatus
from .services import (
    channel_playlist_service,
    subscription_import_service,
    sync_service,
    video_service,
)

logger = logging.getLogger(__name__)
REDIS_SETTINGS = settings.get_redis_settings()
HEARTBEAT_INTERVAL_SECONDS = 30
HEARTBEAT_TTL_SECONDS = 90
SCHEDULER_LOCK_KEY = "chooseyourtube:scheduler:channel-refresh"
SCHEDULER_LOCK_SECONDS = 10 * 60
SCHEDULER_SPREAD_SECONDS = 50 * 60
RETRY_DELAYS_SECONDS = (60, 5 * 60, 30 * 60)
JOB_TIMEOUT_SECONDS = 5 * 60
STALE_RUNNING_AFTER_SECONDS = JOB_TIMEOUT_SECONDS + 5 * 60
RECONCILIATION_LOCK_KEY = "chooseyourtube:worker:sync-reconciliation"
RECONCILIATION_LOCK_SECONDS = 4 * 60
RECONCILIATION_BATCH_SIZE = 200


async def maintain_worker_heartbeat(ctx: dict) -> None:
    while True:
        payload = json.dumps(
            {
                "worker": socket.gethostname(),
                "version": APP_VERSION,
                "seen_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        await ctx["redis"].set(WORKER_HEARTBEAT_KEY, payload, ex=HEARTBEAT_TTL_SECONDS)
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)


async def startup(ctx: dict) -> None:
    ctx["redis"] = await arq.create_pool(REDIS_SETTINGS)
    ctx["heartbeat_task"] = asyncio.create_task(maintain_worker_heartbeat(ctx))
    await reconcile_sync_runs(ctx)


async def shutdown(ctx: dict) -> None:
    heartbeat_task = ctx.get("heartbeat_task")
    if heartbeat_task:
        heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task
    if redis := ctx.get("redis"):
        await redis.close()


def _stagger_seconds(owner_id: str, channel_id: str) -> int:
    digest = hashlib.sha256(f"{owner_id}:{channel_id}".encode()).digest()
    return int.from_bytes(digest[:4], "big") % SCHEDULER_SPREAD_SECONDS


def _reconciliation_defer_seconds(run: SyncRun, now: datetime) -> int:
    if run.next_retry_at is not None:
        next_retry_at = run.next_retry_at
        if next_retry_at.tzinfo is None:
            next_retry_at = next_retry_at.replace(tzinfo=timezone.utc)
        if next_retry_at > now:
            return math.ceil((next_retry_at - now).total_seconds())
    if (
        run.kind == SyncRunKind.CHANNEL_REFRESH.value
        and run.channel_id is not None
        and run.owner_id is not None
    ):
        return _stagger_seconds(str(run.owner_id), run.channel_id)
    return 0


async def reconcile_sync_runs(ctx: dict) -> None:
    redis = ctx["redis"]
    lock_value = str(uuid.uuid4())
    acquired = await redis.set(
        RECONCILIATION_LOCK_KEY,
        lock_value,
        ex=RECONCILIATION_LOCK_SECONDS,
        nx=True,
    )
    if not acquired:
        logger.info("sync_reconciliation_overlap_skipped")
        return

    scanned = requeued = already_present = stale_failed = enqueue_failed = 0
    try:
        now = datetime.now(timezone.utc)
        stale_before = now - timedelta(seconds=STALE_RUNNING_AFTER_SECONDS)
        async with sessionmanager.session() as db:
            stale_runs = list(
                await db.scalars(
                    select(SyncRun)
                    .where(
                        SyncRun.status == SyncRunStatus.RUNNING.value,
                        SyncRun.updated_at < stale_before,
                    )
                    .order_by(SyncRun.updated_at)
                    .limit(RECONCILIATION_BATCH_SIZE)
                    .with_for_update(skip_locked=True)
                )
            )
            for run in stale_runs:
                run.status = SyncRunStatus.FAILED.value
                run.error_code = "WORKER_INTERRUPTED"
                run.error_message = (
                    "Synchronization was interrupted by a worker shutdown."
                )
                run.finished_at = now
                run.next_retry_at = None
                if run.subscription_import_id is not None:
                    import_record = await db.get(
                        SubscriptionImport, run.subscription_import_id
                    )
                    if import_record is not None:
                        import_record.status = "failed"
                        import_record.error_code = "WORKER_INTERRUPTED"
                        import_record.error_message = run.error_message
                        import_record.finished_at = now
                stale_failed += 1
            await db.commit()

            offset = 0
            while True:
                queued_runs = list(
                    await db.scalars(
                        select(SyncRun)
                        .where(SyncRun.status == SyncRunStatus.QUEUED.value)
                        .order_by(SyncRun.queued_at, SyncRun.id)
                        .limit(RECONCILIATION_BATCH_SIZE)
                        .offset(offset)
                    )
                )
                if not queued_runs:
                    break
                for run in queued_runs:
                    scanned += 1
                    try:
                        created = await sync_service.reenqueue_run(
                            redis,
                            run,
                            defer_seconds=_reconciliation_defer_seconds(run, now),
                        )
                        if created:
                            requeued += 1
                        else:
                            already_present += 1
                    except Exception:
                        enqueue_failed += 1
                        logger.exception(
                            "sync_reconciliation_enqueue_failed",
                            extra={"sync_run_id": str(run.id), "task_kind": run.kind},
                        )
                if len(queued_runs) < RECONCILIATION_BATCH_SIZE:
                    break
                offset += RECONCILIATION_BATCH_SIZE
        logger.info(
            "sync_reconciliation_completed",
            extra={
                "scanned": scanned,
                "requeued": requeued,
                "already_present": already_present,
                "stale_failed": stale_failed,
                "enqueue_failed": enqueue_failed,
            },
        )
    finally:
        if await redis.get(RECONCILIATION_LOCK_KEY) in {
            lock_value,
            lock_value.encode(),
        }:
            await redis.delete(RECONCILIATION_LOCK_KEY)


async def enqueue_channel_refreshes(ctx: dict) -> None:
    redis = ctx["redis"]
    lock_value = str(uuid.uuid4())
    acquired = await redis.set(
        SCHEDULER_LOCK_KEY, lock_value, ex=SCHEDULER_LOCK_SECONDS, nx=True
    )
    if not acquired:
        logger.info("scheduler_overlap_skipped")
        return

    try:
        offset = 0
        batch_size = 200
        async with sessionmanager.session() as db:
            while True:
                rows = list(
                    (
                        await db.execute(
                            select(UserChannel.channel_id, UserChannel.user_id)
                            .distinct(UserChannel.channel_id)
                            .order_by(UserChannel.channel_id, UserChannel.user_id)
                            .limit(batch_size)
                            .offset(offset)
                        )
                    ).all()
                )
                if not rows:
                    break
                for channel_id, user_id in rows:
                    try:
                        await sync_service.enqueue_run(
                            db,
                            redis,
                            owner_id=str(user_id),
                            kind=SyncRunKind.CHANNEL_REFRESH,
                            channel_id=channel_id,
                            defer_seconds=_stagger_seconds(str(user_id), channel_id),
                        )
                    except Exception:
                        logger.exception(
                            "scheduled_sync_enqueue_failed",
                            extra={
                                "owner_id": str(user_id),
                                "channel_id": channel_id,
                                "task_kind": SyncRunKind.CHANNEL_REFRESH.value,
                                "outcome": "failed",
                            },
                        )
                    # enqueue_run may roll back after an error; continue with a clean session.
                    if not db.is_active:
                        await db.rollback()
                if len(rows) < batch_size:
                    break
                offset += batch_size
    finally:
        if await redis.get(SCHEDULER_LOCK_KEY) in {lock_value, lock_value.encode()}:
            await redis.delete(SCHEDULER_LOCK_KEY)


async def _execute_kind(
    run, db, youtube_client: YouTubeAPI, redis
) -> sync_service.SyncProgress:
    if run.kind == SyncRunKind.SUBSCRIPTION_IMPORT.value:
        if run.subscription_import_id is None:
            raise ApplicationError(
                "INVALID_SYNC_TARGET", "The subscription import target is invalid.", 422
            )
        return await subscription_import_service.execute_import(
            db,
            redis,
            youtube_client,
            import_id=run.subscription_import_id,
            owner_id=run.owner_id,
        )
    if run.channel_id is None:
        raise ApplicationError(
            "INVALID_SYNC_TARGET", "The synchronization target is invalid.", 422
        )
    if run.kind == SyncRunKind.INITIAL_CHANNEL_SYNC.value:
        progress = await video_service.fetch_initial_channel_videos(
            run.channel_id, db, youtube_client, owner_id=run.owner_id
        )
        playlist_progress = await channel_playlist_service.sync_channel_playlists(
            run.channel_id, db, youtube_client, owner_id=run.owner_id
        )
        progress.add(playlist_progress)
        return progress
    if run.kind == SyncRunKind.CHANNEL_REFRESH.value:
        return await video_service.refresh_latest_channel_videos(
            run.channel_id, db, youtube_client, owner_id=run.owner_id
        )
    if run.kind == SyncRunKind.PLAYLIST_SYNC.value:
        return await channel_playlist_service.sync_channel_playlists(
            run.channel_id, db, youtube_client, owner_id=run.owner_id
        )
    raise ApplicationError(
        "SYNC_KIND_NOT_IMPLEMENTED", "This synchronization type is not available.", 422
    )


async def execute_sync_run(ctx: dict, sync_run_id: str) -> None:
    run_uuid = uuid.UUID(sync_run_id)
    async with sessionmanager.session() as db:
        run = await crud_sync_run.claim_sync_run(db, run_uuid)
        if run is None:
            return

    started = time.perf_counter()
    youtube_client = YouTubeAPI(api_key=settings.YOUTUBE_API_KEY, account_usage=True)
    try:
        async with sessionmanager.session() as db:
            run = await crud_sync_run.get_sync_run(db, run_uuid)
            if run is None:
                return
            progress = await _execute_kind(run, db, youtube_client, ctx["redis"])
            run.items_discovered += progress.discovered
            run.items_created += progress.created
            run.items_updated += progress.updated
            run.items_skipped += progress.skipped
            run.items_failed += progress.failed
            if progress.failed:
                run.status = (
                    SyncRunStatus.FAILED.value
                    if run.kind == SyncRunKind.SUBSCRIPTION_IMPORT.value
                    and not (progress.created or progress.skipped)
                    else SyncRunStatus.PARTIAL.value
                )
                if run.kind == SyncRunKind.SUBSCRIPTION_IMPORT.value:
                    run.error_code = "IMPORT_CANDIDATES_FAILED"
                    run.error_message = "Some selected channels could not be imported."
            else:
                run.status = SyncRunStatus.SUCCEEDED.value
                run.error_code = None
                run.error_message = None
            run.finished_at = datetime.now(timezone.utc)
            run.next_retry_at = None
            await db.commit()
            logger.info(
                "sync_run_completed",
                extra={
                    "sync_run_id": sync_run_id,
                    "task_kind": run.kind,
                    "owner_id": run.owner_id,
                    "channel_id": run.channel_id,
                    "subscription_import_id": (
                        str(run.subscription_import_id)
                        if run.subscription_import_id
                        else None
                    ),
                    "attempt": run.attempt_count,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                    "outcome": run.status,
                    "items_discovered": run.items_discovered,
                    "items_created": run.items_created,
                    "items_updated": run.items_updated,
                    "items_skipped": run.items_skipped,
                    "items_failed": run.items_failed,
                },
            )
    except ApplicationError as exc:
        async with sessionmanager.session() as db:
            run = await crud_sync_run.get_sync_run(db, run_uuid)
            if run is None:
                return
            run.error_code = exc.code
            run.error_message = exc.message
            can_retry = exc.retryable and run.attempt_count < run.max_attempts
            if can_retry:
                delay = RETRY_DELAYS_SECONDS[run.attempt_count - 1]
                run.status = SyncRunStatus.QUEUED.value
                run.next_retry_at = datetime.now(timezone.utc) + timedelta(
                    seconds=delay
                )
                if run.subscription_import_id is not None:
                    await subscription_import_service.defer_execution(
                        db,
                        import_id=run.subscription_import_id,
                        owner_id=run.owner_id,
                        code=exc.code,
                        message=exc.message,
                    )
                await db.commit()
                logger.warning(
                    "sync_run_retry_scheduled",
                    extra={
                        "sync_run_id": sync_run_id,
                        "task_kind": run.kind,
                        "owner_id": run.owner_id,
                        "channel_id": run.channel_id,
                        "subscription_import_id": (
                            str(run.subscription_import_id)
                            if run.subscription_import_id
                            else None
                        ),
                        "attempt": run.attempt_count,
                        "outcome": "retrying",
                    },
                )
                raise arq.Retry(defer=delay) from exc
            if run.subscription_import_id is not None:
                await subscription_import_service.fail_execution(
                    db,
                    import_id=run.subscription_import_id,
                    owner_id=run.owner_id,
                    code=exc.code,
                    message=exc.message,
                )
            run.status = SyncRunStatus.FAILED.value
            run.finished_at = datetime.now(timezone.utc)
            run.next_retry_at = None
            await db.commit()
            logger.warning(
                "sync_run_failed",
                extra={
                    "sync_run_id": sync_run_id,
                    "task_kind": run.kind,
                    "owner_id": run.owner_id,
                    "channel_id": run.channel_id,
                    "subscription_import_id": (
                        str(run.subscription_import_id)
                        if run.subscription_import_id
                        else None
                    ),
                    "attempt": run.attempt_count,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                    "outcome": "failed",
                },
            )
    except Exception as exc:
        logger.exception("sync_run_unexpected_error")
        async with sessionmanager.session() as db:
            run = await crud_sync_run.get_sync_run(db, run_uuid)
            if run is not None:
                if run.subscription_import_id is not None:
                    await subscription_import_service.fail_execution(
                        db,
                        import_id=run.subscription_import_id,
                        owner_id=run.owner_id,
                        code="SYNC_INTERNAL_ERROR",
                        message="The subscription import failed unexpectedly.",
                    )
                run.status = SyncRunStatus.FAILED.value
                run.error_code = "SYNC_INTERNAL_ERROR"
                run.error_message = "Synchronization failed unexpectedly."
                run.finished_at = datetime.now(timezone.utc)
                await db.commit()
        raise exc


class WorkerSettings:
    functions = [execute_sync_run]
    cron_jobs = [
        cron(enqueue_channel_refreshes, minute=0),
        cron(reconcile_sync_runs, minute=set(range(0, 60, 5))),
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = REDIS_SETTINGS
    timezone = timezone.utc
    max_jobs = 10
    job_timeout = JOB_TIMEOUT_SECONDS
    max_tries = 4
    keep_result = 0
