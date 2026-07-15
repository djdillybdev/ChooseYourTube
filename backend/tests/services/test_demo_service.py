from __future__ import annotations

from datetime import datetime, timedelta, timezone
import inspect
import uuid

import pytest
from sqlalchemy import func, select

from app.auth.models import RefreshSession
from app.db.models.channel import Channel
from app.db.models.folder import Folder
from app.db.models.playlist import Playlist
from app.db.models.tag import Tag
from app.db.models.video import Video
from app.services import demo_service


@pytest.mark.asyncio
async def test_seed_demo_is_idempotent_and_restores_mutable_state(db_session):
    owner_id = await demo_service.seed_demo(db_session, email="demo@example.com")

    video = await db_session.scalar(
        select(Video).where(Video.owner_id == owner_id, Video.id == "pLqjQ55tz-U")
    )
    assert video is not None
    video.is_favorited = False
    db_session.add(
        Folder(
            id="user-folder", owner_id=owner_id, name="Recruiter change", position=99
        )
    )
    await db_session.commit()

    repeated_owner = await demo_service.seed_demo(db_session, email="demo@example.com")

    assert repeated_owner == owner_id
    assert (
        await db_session.scalar(
            select(func.count())
            .select_from(Channel)
            .where(Channel.owner_id == owner_id)
        )
        == 4
    )
    assert (
        await db_session.scalar(
            select(func.count()).select_from(Video).where(Video.owner_id == owner_id)
        )
        == 24
    )
    assert (
        await db_session.scalar(
            select(func.count()).select_from(Tag).where(Tag.owner_id == owner_id)
        )
        == 3
    )
    assert (
        await db_session.scalar(
            select(func.count())
            .select_from(Playlist)
            .where(Playlist.owner_id == owner_id)
        )
        == 3
    )
    assert await db_session.get(Folder, "user-folder") is None
    restored = await db_session.scalar(
        select(Video).where(Video.owner_id == owner_id, Video.id == "pLqjQ55tz-U")
    )
    assert restored is not None and restored.is_favorited is True


@pytest.mark.asyncio
async def test_daily_reset_preserves_last_refreshed_video_metadata(db_session):
    owner_id = await demo_service.seed_demo(db_session, email="demo@example.com")
    video = await db_session.scalar(
        select(Video).where(Video.owner_id == owner_id, Video.id == "h6fcK_fRYaI")
    )
    assert video is not None
    video.title = "Metadata from the last successful RSS refresh"
    video.is_favorited = False
    await db_session.commit()

    await demo_service.reset_demo_state(db_session, owner_id=owner_id)

    refreshed = await db_session.scalar(
        select(Video).where(Video.owner_id == owner_id, Video.id == "h6fcK_fRYaI")
    )
    assert refreshed is not None
    assert refreshed.title == "Metadata from the last successful RSS refresh"
    assert refreshed.is_favorited is True


@pytest.mark.asyncio
async def test_cleanup_expired_sessions_preserves_active_session(db_session):
    owner_id = await demo_service.seed_demo(db_session, email="demo@example.com")
    user_id = uuid.UUID(demo_service.load_demo_seed()["user_id"])
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            RefreshSession(
                user_id=user_id,
                session_id=uuid.UUID("77000000-0000-0000-0000-000000000001"),
                token_hash="a" * 64,
                expires_at=now - timedelta(seconds=1),
            ),
            RefreshSession(
                user_id=user_id,
                session_id=uuid.UUID("77000000-0000-0000-0000-000000000002"),
                token_hash="b" * 64,
                expires_at=now + timedelta(days=1),
            ),
        ]
    )
    await db_session.commit()

    assert owner_id
    assert await demo_service.cleanup_expired_sessions(db_session) == 1
    remaining = list(await db_session.scalars(select(RefreshSession)))
    assert len(remaining) == 1
    assert remaining[0].token_hash == "b" * 64


def test_demo_refresh_has_no_data_api_dependency():
    signature = inspect.signature(demo_service.refresh_curated_channels_from_rss)
    assert "youtube_client" not in signature.parameters
    assert not hasattr(demo_service, "YouTubeAPI")


@pytest.mark.asyncio
async def test_demo_rss_refresh_isolates_channel_failures(monkeypatch):
    class SessionContext:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, traceback):
            return False

    from app.db.session import sessionmanager
    from app.services.sync_service import SyncProgress

    monkeypatch.setattr(
        demo_service,
        "load_demo_seed",
        lambda: {"channels": [{"id": "failed"}, {"id": "succeeded"}]},
    )
    monkeypatch.setattr(sessionmanager, "session", lambda: SessionContext())

    async def refresh(channel_id, _db, *, owner_id):
        assert owner_id == "demo-owner"
        if channel_id == "failed":
            raise RuntimeError("feed unavailable")
        return SyncProgress(discovered=1, created=1)

    monkeypatch.setattr(demo_service, "refresh_latest_channel_videos_from_rss", refresh)

    progress = await demo_service.refresh_curated_channels_from_rss("demo-owner")

    assert progress.discovered == 1
    assert progress.created == 1
    assert progress.failed == 1
