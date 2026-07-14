"""Tests for durable synchronization worker configuration and scheduling."""

from datetime import timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.sync_run import SyncRunKind
from app.worker import (
    WorkerSettings,
    RETRY_DELAYS_SECONDS,
    _stagger_seconds,
    enqueue_channel_refreshes,
    execute_sync_run,
    shutdown,
    startup,
)


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
async def test_scheduler_pages_and_enqueues_every_channel(mock_sessionmanager):
    redis = AsyncMock()
    redis.set.return_value = True
    redis.get.side_effect = lambda _key: redis.set.call_args.args[1]
    channels = [MagicMock(id=f"channel-{i}", owner_id=f"owner-{i}") for i in range(200)]
    final = MagicMock(id="channel-final", owner_id="owner-final")

    with (
        patch(
            "app.worker.crud_channel.get_channels",
            new=AsyncMock(side_effect=[channels, [final]]),
        ) as get_channels,
        patch(
            "app.worker.sync_service.enqueue_run", new=AsyncMock()
        ) as enqueue_run,
    ):
        await enqueue_channel_refreshes({"redis": redis})

    assert get_channels.await_count == 2
    assert enqueue_run.await_count == 201
    assert enqueue_run.call_args.kwargs["kind"] == SyncRunKind.CHANNEL_REFRESH
    redis.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_scheduler_isolates_channel_enqueue_failure(mock_sessionmanager):
    redis = AsyncMock()
    redis.set.return_value = True
    redis.get.side_effect = lambda _key: redis.set.call_args.args[1]
    channels = [
        MagicMock(id="broken", owner_id="owner-1"),
        MagicMock(id="healthy", owner_id="owner-2"),
    ]
    with (
        patch(
            "app.worker.crud_channel.get_channels",
            new=AsyncMock(return_value=channels),
        ),
        patch(
            "app.worker.sync_service.enqueue_run",
            new=AsyncMock(side_effect=[RuntimeError("queue"), MagicMock()]),
        ) as enqueue_run,
    ):
        await enqueue_channel_refreshes({"redis": redis})
    assert enqueue_run.await_count == 2
