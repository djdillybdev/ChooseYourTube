import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.crud import crud_sync_run
from app.db.models.channel import Channel
from app.db.models.sync_run import SyncRun, YouTubeAPIUsage
from app.db.models.subscription_import import SubscriptionImport
from app.schemas.sync_run import SyncRunKind, SyncRunStatus
from app.services import sync_service

OWNER_1 = "10000000-0000-0000-0000-000000000001"
OWNER_2 = "10000000-0000-0000-0000-000000000002"


@pytest.fixture
async def channel(db_session):
    row = Channel(
        id="UC_sync_run",
        owner_id=OWNER_1,
        handle="sync-run",
        title="Sync Run",
        uploads_playlist_id="UU_sync_run",
    )
    db_session.add(row)
    await db_session.commit()
    return row


@pytest.mark.asyncio
async def test_create_or_get_active_run_deduplicates(db_session, channel):
    first, created = await sync_service.create_or_get_active_run(
        db_session,
        owner_id=OWNER_1,
        channel_id=channel.id,
        kind=SyncRunKind.CHANNEL_REFRESH,
    )
    second, created_again = await sync_service.create_or_get_active_run(
        db_session,
        owner_id=OWNER_1,
        channel_id=channel.id,
        kind=SyncRunKind.CHANNEL_REFRESH,
    )
    assert created is True
    assert created_again is False
    assert second.id == first.id


@pytest.mark.asyncio
async def test_enqueue_uses_run_id_as_job_id(db_session, channel, mock_arq_redis):
    run = await sync_service.enqueue_run(
        db_session,
        mock_arq_redis,
        owner_id=OWNER_1,
        channel_id=channel.id,
        kind=SyncRunKind.PLAYLIST_SYNC,
    )
    mock_arq_redis.enqueue_job.assert_awaited_once_with(
        "execute_sync_run", str(run.id), _job_id=str(run.id)
    )


@pytest.mark.asyncio
async def test_import_runs_are_deduplicated_by_import(db_session):
    import_record = SubscriptionImport(owner_id=OWNER_1, source="youtube_takeout_csv")
    db_session.add(import_record)
    await db_session.commit()
    first, created = await sync_service.create_or_get_active_run(
        db_session,
        owner_id=OWNER_1,
        subscription_import_id=import_record.id,
        kind=SyncRunKind.SUBSCRIPTION_IMPORT,
    )
    second, created_again = await sync_service.create_or_get_active_run(
        db_session,
        owner_id=OWNER_1,
        subscription_import_id=import_record.id,
        kind=SyncRunKind.SUBSCRIPTION_IMPORT,
    )
    assert created is True
    assert created_again is False
    assert first.id == second.id


@pytest.mark.asyncio
async def test_claim_is_atomic_and_increments_attempt(db_session, channel):
    run, _ = await sync_service.create_or_get_active_run(
        db_session,
        owner_id=OWNER_1,
        channel_id=channel.id,
        kind=SyncRunKind.CHANNEL_REFRESH,
    )
    claimed = await crud_sync_run.claim_sync_run(db_session, run.id)
    duplicate = await crud_sync_run.claim_sync_run(db_session, run.id)
    assert claimed is not None
    assert claimed.status == SyncRunStatus.RUNNING.value
    assert claimed.attempt_count == 1
    assert duplicate is None


@pytest.mark.asyncio
async def test_list_runs_is_owner_scoped(db_session, channel):
    db_session.add_all(
        [
            SyncRun(owner_id=OWNER_1, channel_id=channel.id, kind="channel_refresh"),
            SyncRun(owner_id=OWNER_2, kind="demo_maintenance"),
        ]
    )
    await db_session.commit()
    response = await sync_service.list_runs(
        db_session,
        owner_id=OWNER_1,
        status=None,
        kind=None,
        channel_id=None,
        limit=20,
        offset=0,
    )
    assert response.total == 1
    assert response.items[0].owner_id == OWNER_1


def test_safe_retryability_is_derived_from_classified_code():
    owner_id = uuid.uuid4()
    run = SyncRun(
        id=uuid.uuid4(),
        owner_id=owner_id,
        kind="channel_refresh",
        status="failed",
        error_code="RSS_FETCH_FAILED",
        error_message="The channel feed is temporarily unavailable.",
        attempt_count=4,
        max_attempts=4,
        items_discovered=0,
        items_created=0,
        items_updated=0,
        items_skipped=0,
        items_failed=0,
        queued_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    output = sync_service.to_sync_run_out(run)
    assert output.owner_id == str(owner_id)
    assert output.retryable is True
    run.error_code = "YOUTUBE_QUOTA_EXHAUSTED"
    assert sync_service.to_sync_run_out(run).retryable is False


@pytest.mark.asyncio
async def test_quota_totals_aggregate_all_outcomes(db_session):
    today = datetime.now(timezone.utc).date()
    db_session.add_all(
        [
            YouTubeAPIUsage(
                usage_date=today,
                operation="videos.list",
                outcome="succeeded",
                estimated_units=3,
                call_count=3,
            ),
            YouTubeAPIUsage(
                usage_date=today,
                operation="channels.list",
                outcome="failed",
                estimated_units=1,
                call_count=1,
            ),
        ]
    )
    await db_session.commit()
    assert await crud_sync_run.quota_totals(db_session, today) == (4, 4)


@pytest.mark.asyncio
async def test_unscoped_maintenance_run_is_created(db_session):
    run, created = await sync_service.create_or_get_active_run(
        db_session, owner_id=OWNER_1, kind=SyncRunKind.DEMO_MAINTENANCE
    )
    assert created is True
    assert run.channel_id is None
    assert run.subscription_import_id is None


@pytest.mark.asyncio
async def test_enqueue_supports_defer_deduplication_and_queue_failure(
    db_session, channel, mock_arq_redis
):
    deferred = await sync_service.enqueue_run(
        db_session,
        mock_arq_redis,
        owner_id=OWNER_1,
        channel_id=channel.id,
        kind=SyncRunKind.CHANNEL_REFRESH,
        defer_seconds=42,
    )
    mock_arq_redis.enqueue_job.assert_awaited_once_with(
        "execute_sync_run", str(deferred.id), _job_id=str(deferred.id), _defer_by=42
    )
    mock_arq_redis.enqueue_job.reset_mock()
    duplicate = await sync_service.enqueue_run(
        db_session,
        mock_arq_redis,
        owner_id=OWNER_1,
        channel_id=channel.id,
        kind=SyncRunKind.CHANNEL_REFRESH,
    )
    assert duplicate.id == deferred.id
    mock_arq_redis.enqueue_job.assert_not_awaited()

    deferred.status = SyncRunStatus.SUCCEEDED.value
    await db_session.commit()
    mock_arq_redis.enqueue_job.side_effect = ConnectionError("queue offline")
    with pytest.raises(sync_service.ApplicationError) as error:
        await sync_service.enqueue_run(
            db_session,
            mock_arq_redis,
            owner_id=OWNER_1,
            channel_id=channel.id,
            kind=SyncRunKind.PLAYLIST_SYNC,
        )
    assert error.value.code == "QUEUE_UNAVAILABLE"
    failed = await crud_sync_run.get_active_sync_run(
        db_session,
        owner_id=OWNER_1,
        channel_id=channel.id,
        subscription_import_id=None,
        kind=SyncRunKind.PLAYLIST_SYNC.value,
    )
    assert failed is None


@pytest.mark.asyncio
async def test_integrity_race_returns_winner_or_reraises():
    existing = MagicMock()
    db = AsyncMock()
    db.add = MagicMock()
    db.commit.side_effect = IntegrityError("insert", {}, RuntimeError("duplicate"))
    with patch(
        "app.services.sync_service.crud_sync_run.get_active_sync_run",
        new=AsyncMock(side_effect=[None, existing]),
    ):
        run, created = await sync_service.create_or_get_active_run(
            db,
            owner_id=OWNER_1,
            channel_id="channel",
            kind=SyncRunKind.CHANNEL_REFRESH,
        )
    assert (run, created) == (existing, False)
    db.rollback.assert_awaited_once()

    db.commit.side_effect = IntegrityError("insert", {}, RuntimeError("duplicate"))
    with (
        patch(
            "app.services.sync_service.crud_sync_run.get_active_sync_run",
            new=AsyncMock(side_effect=[None, None]),
        ),
        pytest.raises(IntegrityError),
    ):
        await sync_service.create_or_get_active_run(
            db,
            owner_id=OWNER_1,
            channel_id="channel",
            kind=SyncRunKind.CHANNEL_REFRESH,
        )

    db.commit.side_effect = IntegrityError("insert", {}, RuntimeError("duplicate"))
    with pytest.raises(IntegrityError):
        await sync_service.create_or_get_active_run(
            db, owner_id=OWNER_1, kind=SyncRunKind.DEMO_MAINTENANCE
        )


@pytest.mark.asyncio
async def test_owned_lookup_and_retry_success(db_session, channel, mock_arq_redis):
    with pytest.raises(sync_service.ApplicationError) as missing:
        await sync_service.get_owned_run(db_session, uuid.uuid4(), OWNER_1)
    assert missing.value.code == "NOT_FOUND"

    previous = SyncRun(
        owner_id=OWNER_1,
        channel_id=channel.id,
        kind=SyncRunKind.CHANNEL_REFRESH.value,
        status=SyncRunStatus.FAILED.value,
        error_code="RSS_FETCH_FAILED",
    )
    db_session.add(previous)
    await db_session.commit()
    retried = await sync_service.retry_run(
        db_session,
        mock_arq_redis,
        sync_run_id=previous.id,
        owner_id=OWNER_1,
    )
    assert retried.status == SyncRunStatus.QUEUED.value
    mock_arq_redis.enqueue_job.assert_awaited_once()
