import uuid
from datetime import datetime, timezone

import pytest

from app.db.crud import crud_sync_run
from app.db.models.channel import Channel
from app.db.models.sync_run import SyncRun, YouTubeAPIUsage
from app.db.models.subscription_import import SubscriptionImport
from app.schemas.sync_run import SyncRunKind, SyncRunStatus
from app.services import sync_service


@pytest.fixture
async def channel(db_session):
    row = Channel(
        id="UC_sync_run",
        owner_id="owner-1",
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
        owner_id=channel.owner_id,
        channel_id=channel.id,
        kind=SyncRunKind.CHANNEL_REFRESH,
    )
    second, created_again = await sync_service.create_or_get_active_run(
        db_session,
        owner_id=channel.owner_id,
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
        owner_id=channel.owner_id,
        channel_id=channel.id,
        kind=SyncRunKind.PLAYLIST_SYNC,
    )
    mock_arq_redis.enqueue_job.assert_awaited_once_with(
        "execute_sync_run", str(run.id), _job_id=str(run.id)
    )


@pytest.mark.asyncio
async def test_import_runs_are_deduplicated_by_import(db_session):
    import_record = SubscriptionImport(owner_id="owner-1", source="youtube_takeout_csv")
    db_session.add(import_record)
    await db_session.commit()
    first, created = await sync_service.create_or_get_active_run(
        db_session,
        owner_id="owner-1",
        subscription_import_id=import_record.id,
        kind=SyncRunKind.SUBSCRIPTION_IMPORT,
    )
    second, created_again = await sync_service.create_or_get_active_run(
        db_session,
        owner_id="owner-1",
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
        owner_id=channel.owner_id,
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
            SyncRun(owner_id="owner-1", channel_id=channel.id, kind="channel_refresh"),
            SyncRun(owner_id="owner-2", kind="demo_maintenance"),
        ]
    )
    await db_session.commit()
    response = await sync_service.list_runs(
        db_session,
        owner_id="owner-1",
        status=None,
        kind=None,
        channel_id=None,
        limit=20,
        offset=0,
    )
    assert response.total == 1
    assert response.items[0].owner_id == "owner-1"


def test_safe_retryability_is_derived_from_classified_code():
    run = SyncRun(
        id=uuid.uuid4(),
        owner_id="owner",
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
    assert sync_service.to_sync_run_out(run).retryable is True
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
