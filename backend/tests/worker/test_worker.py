"""Tests for durable synchronization worker configuration and scheduling."""

import asyncio
from contextlib import asynccontextmanager
from datetime import timezone
from unittest.mock import AsyncMock, MagicMock, patch

import arq
import pytest

from app.core.errors import ApplicationError
from app.db.models.channel import Channel
from app.db.models.subscription_import import SubscriptionImport
from app.db.models.sync_run import SyncRun
from app.schemas.sync_run import SyncRunKind, SyncRunStatus
from app.services.sync_service import SyncProgress
from app.worker import (
    WorkerSettings,
    RETRY_DELAYS_SECONDS,
    _execute_kind,
    _stagger_seconds,
    enqueue_channel_refreshes,
    execute_sync_run,
    maintain_worker_heartbeat,
    shutdown,
    startup,
)

WORKER_OWNER_ID = "30000000-0000-0000-0000-000000000099"


def _rows_result(rows):
    result = MagicMock()
    result.all.return_value = rows
    return result


class TestWorkerSettings:
    def test_only_common_durable_runner_is_registered(self):
        assert WorkerSettings.functions == [execute_sync_run]

    def test_scheduler_runs_hourly_in_utc(self):
        assert len(WorkerSettings.cron_jobs) == 1
        assert WorkerSettings.cron_jobs[0].minute == 0
        assert WorkerSettings.timezone == timezone.utc

    def test_runtime_limits(self):
        assert WorkerSettings.max_jobs == 10
        assert WorkerSettings.max_tries == 4
        assert WorkerSettings.keep_result == 0
        assert RETRY_DELAYS_SECONDS == (60, 300, 1800)


@pytest.mark.asyncio
async def test_startup_and_shutdown_manage_pool_and_heartbeat(mock_arq_pool):
    ctx = {}
    await startup(ctx)
    assert ctx["redis"] == mock_arq_pool
    assert "heartbeat_task" in ctx
    await shutdown(ctx)


@pytest.mark.asyncio
async def test_shutdown_without_started_resources_is_safe():
    await shutdown({})


@pytest.mark.asyncio
async def test_heartbeat_writes_identity_and_ttl():
    redis = AsyncMock()
    with patch("app.worker.asyncio.sleep", new=AsyncMock(side_effect=asyncio.CancelledError)):
        with pytest.raises(asyncio.CancelledError):
            await maintain_worker_heartbeat({"redis": redis})
    redis.set.assert_awaited_once()
    assert redis.set.call_args.kwargs["ex"] == 90


def test_stagger_is_stable_and_bounded():
    first = _stagger_seconds("owner", "channel")
    assert first == _stagger_seconds("owner", "channel")
    assert 0 <= first < 50 * 60


@pytest.mark.asyncio
async def test_scheduler_skips_when_lock_is_held():
    redis = AsyncMock()
    redis.set.return_value = False
    await enqueue_channel_refreshes({"redis": redis})
    redis.get.assert_not_called()


@pytest.mark.asyncio
async def test_scheduler_handles_empty_page_and_does_not_delete_foreign_lock(
    mock_sessionmanager,
):
    redis = AsyncMock()
    redis.set.return_value = True
    redis.get.return_value = b"another-scheduler"
    db = mock_sessionmanager.session.return_value.__aenter__.return_value
    db.execute.return_value = _rows_result([])
    await enqueue_channel_refreshes({"redis": redis})
    redis.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_scheduler_pages_and_enqueues_every_channel(mock_sessionmanager):
    redis = AsyncMock()
    redis.set.return_value = True
    redis.get.side_effect = lambda _key: redis.set.call_args.args[1]
    channels = [(f"channel-{i}", f"owner-{i}") for i in range(200)]
    final = ("channel-final", "owner-final")
    db = mock_sessionmanager.session.return_value.__aenter__.return_value
    db.execute.side_effect = [_rows_result(channels), _rows_result([final])]

    with patch(
        "app.worker.sync_service.enqueue_run", new=AsyncMock()
    ) as enqueue_run:
        await enqueue_channel_refreshes({"redis": redis})

    assert db.execute.await_count == 2
    assert enqueue_run.await_count == 201
    assert enqueue_run.call_args.kwargs["kind"] == SyncRunKind.CHANNEL_REFRESH
    redis.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_scheduler_isolates_channel_enqueue_failure(mock_sessionmanager):
    redis = AsyncMock()
    redis.set.return_value = True
    redis.get.side_effect = lambda _key: redis.set.call_args.args[1]
    channels = [("broken", "owner-1"), ("healthy", "owner-2")]
    db = mock_sessionmanager.session.return_value.__aenter__.return_value
    db.execute.return_value = _rows_result(channels)
    with patch(
        "app.worker.sync_service.enqueue_run",
        new=AsyncMock(side_effect=[RuntimeError("queue"), MagicMock()]),
    ) as enqueue_run:
        db.is_active = False
        await enqueue_channel_refreshes({"redis": redis})
    assert enqueue_run.await_count == 2
    db.rollback.assert_awaited()


def _session_factory(db_session):
    @asynccontextmanager
    async def session():
        yield db_session

    return session


async def _queued_channel_run(db_session, *, attempt_count: int = 0) -> SyncRun:
    channel = Channel(
        id=f"UC_worker_{attempt_count}",
        owner_id=WORKER_OWNER_ID,
        handle=f"worker-{attempt_count}",
        title="Worker test",
        uploads_playlist_id=f"UU_worker_{attempt_count}",
    )
    run = SyncRun(
        owner_id=WORKER_OWNER_ID,
        channel_id=channel.id,
        kind=SyncRunKind.CHANNEL_REFRESH.value,
        status=SyncRunStatus.QUEUED.value,
        attempt_count=attempt_count,
        max_attempts=4,
    )
    db_session.add_all([channel, run])
    await db_session.commit()
    await db_session.refresh(run)
    return run


@pytest.mark.asyncio
async def test_execute_sync_run_records_success_counters(db_session):
    run = await _queued_channel_run(db_session)
    with (
        patch("app.worker.sessionmanager.session", new=_session_factory(db_session)),
        patch("app.worker.YouTubeAPI"),
        patch(
            "app.worker._execute_kind",
            new=AsyncMock(
                return_value=SyncProgress(
                    discovered=5, created=2, updated=1, skipped=2, failed=0
                )
            ),
        ),
    ):
        await execute_sync_run({"redis": AsyncMock()}, str(run.id))

    await db_session.refresh(run)
    assert run.status == SyncRunStatus.SUCCEEDED.value
    assert (run.items_discovered, run.items_created, run.items_updated) == (5, 2, 1)
    assert run.finished_at is not None
    assert run.error_code is None


@pytest.mark.asyncio
async def test_execute_sync_run_records_partial_channel_progress(db_session):
    run = await _queued_channel_run(db_session)
    with (
        patch("app.worker.sessionmanager.session", new=_session_factory(db_session)),
        patch("app.worker.YouTubeAPI"),
        patch(
            "app.worker._execute_kind",
            new=AsyncMock(return_value=SyncProgress(created=1, failed=1)),
        ),
    ):
        await execute_sync_run({"redis": AsyncMock()}, str(run.id))

    await db_session.refresh(run)
    assert run.status == SyncRunStatus.PARTIAL.value
    assert run.items_created == 1
    assert run.items_failed == 1


@pytest.mark.asyncio
async def test_execute_sync_run_marks_all_failed_import(db_session):
    import_record = SubscriptionImport(
        owner_id=WORKER_OWNER_ID, source="youtube_takeout_csv", status="queued"
    )
    db_session.add(import_record)
    await db_session.flush()
    run = SyncRun(
        owner_id=WORKER_OWNER_ID,
        subscription_import_id=import_record.id,
        kind=SyncRunKind.SUBSCRIPTION_IMPORT.value,
        status=SyncRunStatus.QUEUED.value,
    )
    db_session.add(run)
    await db_session.commit()
    with (
        patch("app.worker.sessionmanager.session", new=_session_factory(db_session)),
        patch("app.worker.YouTubeAPI"),
        patch(
            "app.worker._execute_kind",
            new=AsyncMock(return_value=SyncProgress(failed=2)),
        ),
    ):
        await execute_sync_run({"redis": AsyncMock()}, str(run.id))
    await db_session.refresh(run)
    assert run.status == SyncRunStatus.FAILED.value
    assert run.error_code == "IMPORT_CANDIDATES_FAILED"


@pytest.mark.asyncio
async def test_execute_sync_run_schedules_retryable_failure(db_session):
    run = await _queued_channel_run(db_session)
    with (
        patch("app.worker.sessionmanager.session", new=_session_factory(db_session)),
        patch("app.worker.YouTubeAPI"),
        patch(
            "app.worker._execute_kind",
            new=AsyncMock(
                side_effect=ApplicationError(
                    "UPSTREAM_TIMEOUT", "YouTube timed out.", 503, retryable=True
                )
            ),
        ),
    ):
        with pytest.raises(arq.Retry):
            await execute_sync_run({"redis": AsyncMock()}, str(run.id))

    await db_session.refresh(run)
    assert run.status == SyncRunStatus.QUEUED.value
    assert run.error_code == "UPSTREAM_TIMEOUT"
    assert run.next_retry_at is not None
    assert run.finished_at is None


@pytest.mark.asyncio
async def test_execute_sync_run_stops_nonretryable_and_exhausted_failures(db_session):
    nonretryable = await _queued_channel_run(db_session)
    exhausted = await _queued_channel_run(db_session, attempt_count=3)

    for run, error in (
        (
            nonretryable,
            ApplicationError("YOUTUBE_QUOTA_EXHAUSTED", "Quota exhausted.", 429),
        ),
        (
            exhausted,
            ApplicationError("UPSTREAM_TIMEOUT", "Timed out.", 503, retryable=True),
        ),
    ):
        with (
            patch("app.worker.sessionmanager.session", new=_session_factory(db_session)),
            patch("app.worker.YouTubeAPI"),
            patch("app.worker._execute_kind", new=AsyncMock(side_effect=error)),
        ):
            await execute_sync_run({"redis": AsyncMock()}, str(run.id))
        await db_session.refresh(run)
        assert run.status == SyncRunStatus.FAILED.value
        assert run.finished_at is not None
        assert run.next_retry_at is None


@pytest.mark.asyncio
async def test_execute_sync_run_marks_unexpected_import_failure(db_session):
    import_record = SubscriptionImport(
        owner_id=WORKER_OWNER_ID, source="youtube_takeout_csv", status="queued"
    )
    db_session.add(import_record)
    await db_session.flush()
    run = SyncRun(
        owner_id=WORKER_OWNER_ID,
        subscription_import_id=import_record.id,
        kind=SyncRunKind.SUBSCRIPTION_IMPORT.value,
        status=SyncRunStatus.QUEUED.value,
    )
    db_session.add(run)
    await db_session.commit()
    with (
        patch("app.worker.sessionmanager.session", new=_session_factory(db_session)),
        patch("app.worker.YouTubeAPI"),
        patch("app.worker._execute_kind", new=AsyncMock(side_effect=RuntimeError("boom"))),
    ):
        with pytest.raises(RuntimeError, match="boom"):
            await execute_sync_run({"redis": AsyncMock()}, str(run.id))

    await db_session.refresh(run)
    await db_session.refresh(import_record)
    assert run.status == SyncRunStatus.FAILED.value
    assert run.error_code == "SYNC_INTERNAL_ERROR"
    assert import_record.status == "failed"


@pytest.mark.asyncio
async def test_duplicate_delivery_does_not_execute_again(db_session):
    run = await _queued_channel_run(db_session)
    run.status = SyncRunStatus.SUCCEEDED.value
    await db_session.commit()
    execute_kind = AsyncMock()
    with (
        patch("app.worker.sessionmanager.session", new=_session_factory(db_session)),
        patch("app.worker._execute_kind", new=execute_kind),
    ):
        await execute_sync_run({"redis": AsyncMock()}, str(run.id))
    execute_kind.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_kind_dispatches_all_supported_work(db_session):
    redis = AsyncMock()
    youtube = MagicMock()
    channel_run = MagicMock(
        channel_id="UC_dispatch",
        owner_id="owner",
        subscription_import_id=None,
    )

    with (
        patch(
            "app.worker.video_service.fetch_initial_channel_videos",
            new=AsyncMock(return_value=SyncProgress(created=1)),
        ) as initial,
        patch(
            "app.worker.video_service.refresh_latest_channel_videos",
            new=AsyncMock(return_value=SyncProgress(updated=1)),
        ) as refresh,
        patch(
            "app.worker.channel_playlist_service.sync_channel_playlists",
            new=AsyncMock(return_value=SyncProgress(skipped=1)),
        ),
        patch(
            "app.worker.subscription_import_service.execute_import",
            new=AsyncMock(return_value=SyncProgress(discovered=1)),
        ) as import_work,
    ):
        channel_run.kind = SyncRunKind.INITIAL_CHANNEL_SYNC.value
        progress = await _execute_kind(channel_run, db_session, youtube, redis)
        assert (progress.created, progress.skipped) == (1, 1)
        initial.assert_awaited_once()

        channel_run.kind = SyncRunKind.CHANNEL_REFRESH.value
        assert (await _execute_kind(channel_run, db_session, youtube, redis)).updated == 1
        refresh.assert_awaited_once()

        channel_run.kind = SyncRunKind.PLAYLIST_SYNC.value
        assert (await _execute_kind(channel_run, db_session, youtube, redis)).skipped == 1

        channel_run.kind = SyncRunKind.SUBSCRIPTION_IMPORT.value
        channel_run.subscription_import_id = MagicMock()
        await _execute_kind(channel_run, db_session, youtube, redis)
        import_work.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_kind_rejects_missing_and_unknown_targets(db_session):
    run = MagicMock(owner_id="owner", channel_id=None, subscription_import_id=None)
    run.kind = SyncRunKind.SUBSCRIPTION_IMPORT.value
    with pytest.raises(ApplicationError, match="subscription import target"):
        await _execute_kind(run, db_session, MagicMock(), AsyncMock())

    run.kind = SyncRunKind.CHANNEL_REFRESH.value
    with pytest.raises(ApplicationError, match="synchronization target"):
        await _execute_kind(run, db_session, MagicMock(), AsyncMock())

    run.channel_id = "UC_unknown"
    run.kind = SyncRunKind.DEMO_MAINTENANCE.value
    with pytest.raises(ApplicationError, match="not available"):
        await _execute_kind(run, db_session, MagicMock(), AsyncMock())
