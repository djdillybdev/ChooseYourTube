from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import logging
import socket
import time
import uuid
from datetime import datetime, timedelta, timezone

import arq
from arq import cron

from .clients.youtube import YouTubeAPI
from .core.config import settings
from .core.errors import ApplicationError
from .db.crud import crud_channel, crud_sync_run
from .db.session import sessionmanager
from .routers.health import WORKER_HEARTBEAT_KEY
from .schemas.sync_run import SyncRunKind, SyncRunStatus
from .services import channel_playlist_service, sync_service, video_service

logger = logging.getLogger(__name__)
REDIS_SETTINGS = settings.get_redis_settings()
HEARTBEAT_INTERVAL_SECONDS = 30
HEARTBEAT_TTL_SECONDS = 90
SCHEDULER_LOCK_KEY = "chooseyourtube:scheduler:channel-refresh"
SCHEDULER_LOCK_SECONDS = 10 * 60
SCHEDULER_SPREAD_SECONDS = 50 * 60
RETRY_DELAYS_SECONDS = (60, 5 * 60, 30 * 60)


async def maintain_worker_heartbeat(ctx: dict) -> None:
    while True:
        payload = json.dumps(
            {
                "worker": socket.gethostname(),
                "version": "0.1.0",
                "seen_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        await ctx["redis"].set(
            WORKER_HEARTBEAT_KEY, payload, ex=HEARTBEAT_TTL_SECONDS
        )
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)


async def startup(ctx: dict) -> None:
    ctx["redis"] = await arq.create_pool(REDIS_SETTINGS)
    ctx["heartbeat_task"] = asyncio.create_task(maintain_worker_heartbeat(ctx))


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
                channels = await crud_channel.get_channels(
                    db,
                    owner_id=None,
                    limit=batch_size,
                    offset=offset,
                    order_by="owner_id",
                    order_direction="asc",
                )
                if not channels:
                    break
                for channel in channels:
                    try:
                        await sync_service.enqueue_run(
                            db,
                            redis,
                            owner_id=channel.owner_id,
                            kind=SyncRunKind.CHANNEL_REFRESH,
                            channel_id=channel.id,
                            defer_seconds=_stagger_seconds(
                                channel.owner_id, channel.id
                            ),
                        )
                    except Exception:
                        logger.exception(
                            "scheduled_sync_enqueue_failed",
                            extra={
                                "owner_id": channel.owner_id,
                                "channel_id": channel.id,
                                "task_kind": SyncRunKind.CHANNEL_REFRESH.value,
                                "outcome": "failed",
                            },
                        )
                    # enqueue_run may roll back after an error; continue with a clean session.
                    if not db.is_active:
                        await db.rollback()
                if len(channels) < batch_size:
                    break
                offset += batch_size
    finally:
        if await redis.get(SCHEDULER_LOCK_KEY) in {lock_value, lock_value.encode()}:
            await redis.delete(SCHEDULER_LOCK_KEY)


async def _execute_kind(run, db, youtube_client: YouTubeAPI) -> sync_service.SyncProgress:
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
    youtube_client = YouTubeAPI(
        api_key=settings.YOUTUBE_API_KEY, account_usage=True
    )
    try:
        async with sessionmanager.session() as db:
            run = await crud_sync_run.get_sync_run(db, run_uuid)
            if run is None:
                return
            progress = await _execute_kind(run, db, youtube_client)
            run.items_discovered += progress.discovered
            run.items_created += progress.created
            run.items_updated += progress.updated
            run.items_skipped += progress.skipped
            run.items_failed += progress.failed
            run.status = (
                SyncRunStatus.PARTIAL.value
                if progress.failed
                else SyncRunStatus.SUCCEEDED.value
            )
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
                run.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
                await db.commit()
                logger.warning(
                    "sync_run_retry_scheduled",
                    extra={
                        "sync_run_id": sync_run_id,
                        "task_kind": run.kind,
                        "owner_id": run.owner_id,
                        "channel_id": run.channel_id,
                        "attempt": run.attempt_count,
                        "outcome": "retrying",
                    },
                )
                raise arq.Retry(defer=delay) from exc
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
                run.status = SyncRunStatus.FAILED.value
                run.error_code = "SYNC_INTERNAL_ERROR"
                run.error_message = "Synchronization failed unexpectedly."
                run.finished_at = datetime.now(timezone.utc)
                await db.commit()
        raise exc


class WorkerSettings:
    functions = [execute_sync_run]
    cron_jobs = [cron(enqueue_channel_refreshes, minute=0)]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = REDIS_SETTINGS
    timezone = timezone.utc
    max_jobs = 10
    max_tries = 4
    keep_result = 0
