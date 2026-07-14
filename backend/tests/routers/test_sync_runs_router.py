import uuid

import pytest

from app.db.models.sync_run import SyncRun


@pytest.mark.asyncio
async def test_sync_run_list_and_detail_are_owner_scoped(test_client, db_session):
    owned = SyncRun(owner_id="test-user", kind="demo_maintenance")
    other = SyncRun(owner_id="other-user", kind="demo_maintenance")
    db_session.add_all([owned, other])
    await db_session.commit()

    response = test_client.get("/sync-runs")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert test_client.get(f"/sync-runs/{owned.id}").status_code == 200
    assert test_client.get(f"/sync-runs/{other.id}").status_code == 404


@pytest.mark.asyncio
async def test_sync_run_filters(test_client, db_session):
    db_session.add_all(
        [
            SyncRun(owner_id="test-user", kind="channel_refresh", status="failed"),
            SyncRun(owner_id="test-user", kind="playlist_sync", status="succeeded"),
        ]
    )
    await db_session.commit()
    response = test_client.get("/sync-runs?status=failed&kind=channel_refresh")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_retry_rejects_nonretryable_run(test_client, db_session):
    run = SyncRun(
        id=uuid.uuid4(),
        owner_id="test-user",
        kind="demo_maintenance",
        status="failed",
        error_code="YOUTUBE_QUOTA_EXHAUSTED",
    )
    db_session.add(run)
    await db_session.commit()
    response = test_client.post(f"/sync-runs/{run.id}/retry")
    assert response.status_code == 409
    assert response.json()["code"] == "SYNC_NOT_RETRYABLE"


def test_quota_status_is_aggregate_and_safe(test_client):
    response = test_client.get("/sync-runs/quota")
    assert response.status_code == 200
    assert set(response.json()) == {
        "date",
        "budget",
        "estimated_units_used",
        "estimated_units_remaining",
        "call_count",
        "exhausted",
    }
