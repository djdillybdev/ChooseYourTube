from __future__ import annotations

import uuid

import pytest

from app.core.errors import ApplicationError
from app.routers import demo_maintenance
from app.schemas.sync_run import SyncRunStatus
from app.services import demo_service
from app.services.sync_service import SyncProgress


@pytest.mark.asyncio
async def test_maintenance_requires_cron_secret(db_session, monkeypatch):
    monkeypatch.setattr(demo_maintenance.settings, "CRON_SECRET", "s" * 32)

    with pytest.raises(ApplicationError, match="Cron authorization failed"):
        await demo_maintenance.maintain_demo("Bearer wrong", db_session)


@pytest.mark.asyncio
async def test_maintenance_resets_state_and_is_idempotent(db_session, monkeypatch):
    await demo_service.seed_demo(db_session, email="demo@example.com")
    monkeypatch.setattr(
        demo_maintenance.settings, "DEMO_USER_EMAIL", "demo@example.com"
    )
    monkeypatch.setattr(demo_maintenance.settings, "CRON_SECRET", "s" * 32)

    async def refresh(_owner_id: str) -> SyncProgress:
        return SyncProgress(discovered=4, updated=4)

    monkeypatch.setattr(demo_service, "refresh_curated_channels_from_rss", refresh)
    first = await demo_maintenance.maintain_demo("Bearer " + "s" * 32, db_session)
    second = await demo_maintenance.maintain_demo("Bearer " + "s" * 32, db_session)

    assert first.status == SyncRunStatus.SUCCEEDED
    assert first.items_updated == 4
    assert second.id == first.id
    assert second.attempt_count == 1


@pytest.mark.asyncio
async def test_maintenance_is_partial_when_a_feed_is_unavailable(
    db_session, monkeypatch
):
    await demo_service.seed_demo(db_session, email="demo@example.com")
    monkeypatch.setattr(
        demo_maintenance.settings, "DEMO_USER_EMAIL", "demo@example.com"
    )
    monkeypatch.setattr(demo_maintenance.settings, "CRON_SECRET", "s" * 32)
    monkeypatch.setattr(
        demo_service,
        "maintenance_run_id",
        lambda: uuid.UUID("78000000-0000-0000-0000-000000000001"),
    )

    async def unavailable(_owner_id: str) -> SyncProgress:
        raise ApplicationError("RSS_FETCH_FAILED", "A feed is unavailable.", 503)

    monkeypatch.setattr(demo_service, "refresh_curated_channels_from_rss", unavailable)
    result = await demo_maintenance.maintain_demo("Bearer " + "s" * 32, db_session)

    assert result.status == SyncRunStatus.PARTIAL
    assert result.error_code == "RSS_FETCH_FAILED"
