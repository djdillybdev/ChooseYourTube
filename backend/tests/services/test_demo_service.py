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
from app.db.models.subscription_import import (
    SubscriptionImport,
    SubscriptionImportCandidate,
)
from app.db.models.tag import Tag
from app.db.models.video import Video
from app.db.models.user_state import UserChannel, UserVideoState
from app.services import demo_service


EXPECTED_CHANNELS = {
    "UCsXVk37bltHxD1rDPwtNM8Q": "kurzgesagt",
    "UCq8ZAAsI89IoJ-fn1gYpO3g": "nightshift_kurzgesagt",
    "UCzR-rom72PHN9Zg7RML9EbA": "eons",
    "UCsBjURrPoezykLs9EqgamOA": "Fireship",
    "UC4eYXhJI4-7wSWc8UNRwD4A": "nprmusic",
    "UC7_gcs09iThXybpVgjHZ_7g": "pbsspacetime",
    "UCKy1dAqELo0zrOtPkf0eTMw": "IGN",
}


def test_demo_catalog_is_a_complete_real_rss_snapshot():
    catalog = demo_service.load_demo_seed()

    assert catalog["version"] == 2
    assert {
        channel["id"]: channel["handle"] for channel in catalog["channels"]
    } == EXPECTED_CHANNELS

    videos = [video for channel in catalog["channels"] for video in channel["videos"]]
    video_ids = {video["id"] for video in videos}
    assert len(videos) == 42
    assert len(video_ids) == 42
    assert all(len(channel["videos"]) == 6 for channel in catalog["channels"])
    assert all(not video["id"].startswith("cyt") for video in videos)
    assert all(
        {
            "id",
            "title",
            "description",
            "thumbnail_url",
            "published_at",
            "duration_seconds",
            "is_short",
            "source_url",
            "yt_tags",
        }
        <= video.keys()
        for video in videos
    )

    referenced_ids = set(catalog["video_tag_ids"])
    referenced_ids.update(catalog["watched_ids"])
    referenced_ids.update(catalog["favorite_ids"])
    referenced_ids.update(catalog["watch_later_ids"])
    for playlist in catalog["playlists"]:
        referenced_ids.update(playlist["video_ids"])
    assert referenced_ids <= video_ids


@pytest.mark.asyncio
async def test_seed_demo_is_idempotent_and_restores_mutable_state(db_session):
    owner_id = await demo_service.seed_demo(db_session, email="demo@example.com")
    catalog = demo_service.load_demo_seed()
    favorite_id = catalog["favorite_ids"][0]

    uid = uuid.UUID(owner_id)
    state = await db_session.get(UserVideoState, (uid, favorite_id))
    assert state is not None
    state.is_favorited = False
    db_session.add(
        Folder(id="user-folder", owner_id=owner_id, name="Change", position=99)
    )
    db_session.add(
        Channel(
            id="UC-retired-demo-channel",
            title="Retired demo channel",
            handle="retired-demo-channel",
            uploads_playlist_id="UU-retired-demo-channel",
        )
    )
    db_session.add(
        UserChannel(user_id=uid, channel_id="UC-retired-demo-channel")
    )
    db_session.add(
        Video(
            id="retiredVid1",
            channel_id="UC-retired-demo-channel",
            title="Retired demo video",
        )
    )
    await db_session.commit()

    repeated_owner = await demo_service.seed_demo(db_session, email="demo@example.com")

    assert repeated_owner == owner_id
    assert (
        await db_session.scalar(
            select(func.count())
            .select_from(UserChannel)
            .where(UserChannel.user_id == uid)
        )
        == 7
    )
    assert (
        await db_session.scalar(
            select(func.count())
            .select_from(Video)
            .join(UserChannel, UserChannel.channel_id == Video.channel_id)
            .where(UserChannel.user_id == uid)
        )
        == 42
    )
    assert (
        await db_session.scalar(
            select(func.count()).select_from(Tag).where(Tag.owner_id == owner_id)
        )
        == 5
    )
    assert (
        await db_session.scalar(
            select(func.count()).select_from(Folder).where(Folder.owner_id == owner_id)
        )
        == 4
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
    assert (
        await db_session.scalar(
            select(UserChannel).where(
                UserChannel.user_id == uid,
                UserChannel.channel_id == "UC-retired-demo-channel",
            )
        )
        is None
    )
    restored = await db_session.get(UserVideoState, (uid, favorite_id))
    assert restored is not None and restored.is_favorited is True

    imported = await db_session.get(SubscriptionImport, demo_service.IMPORT_ID)
    assert imported is not None
    assert imported.candidate_count == 7
    assert imported.new_count == 7
    assert imported.selected_count == 7
    assert imported.imported_count == 7
    candidates = list(
        await db_session.scalars(
            select(SubscriptionImportCandidate)
            .where(SubscriptionImportCandidate.import_id == demo_service.IMPORT_ID)
            .order_by(SubscriptionImportCandidate.source_index)
        )
    )
    assert [candidate.channel_id for candidate in candidates] == list(EXPECTED_CHANNELS)


@pytest.mark.asyncio
async def test_daily_reset_preserves_last_refreshed_video_metadata(db_session):
    owner_id = await demo_service.seed_demo(db_session, email="demo@example.com")
    catalog = demo_service.load_demo_seed()
    favorite_id = catalog["favorite_ids"][0]
    channel_id = catalog["channels"][0]["id"]
    uid = uuid.UUID(owner_id)
    video = await db_session.get(Video, favorite_id)
    assert video is not None
    video.title = "Metadata from the last successful RSS refresh"
    state = await db_session.get(UserVideoState, (uid, favorite_id))
    assert state is not None
    state.is_favorited = False
    db_session.add(
        Video(
            id="rssAddedVid",
            channel_id=channel_id,
            title="A video discovered after the pinned snapshot",
        )
    )
    db_session.add(
        Channel(
            id="UC-uncatalogued-channel",
            title="Uncatalogued channel",
            handle="uncatalogued-channel",
            uploads_playlist_id="UU-uncatalogued-channel",
        )
    )
    db_session.add(
        UserChannel(user_id=uid, channel_id="UC-uncatalogued-channel")
    )
    db_session.add(
        Video(
            id="uncatalogued",
            channel_id="UC-uncatalogued-channel",
            title="This content should be removed",
        )
    )
    await db_session.commit()

    await demo_service.reset_demo_state(db_session, owner_id=owner_id)

    refreshed = await db_session.get(Video, favorite_id)
    assert refreshed is not None
    assert refreshed.title == "Metadata from the last successful RSS refresh"
    refreshed_state = await db_session.get(UserVideoState, (uid, favorite_id))
    assert refreshed_state is not None and refreshed_state.is_favorited is True
    assert (
        await db_session.scalar(
            select(Video)
            .join(UserChannel, UserChannel.channel_id == Video.channel_id)
            .where(UserChannel.user_id == uid, Video.id == "rssAddedVid")
        )
        is not None
    )
    assert (
        await db_session.scalar(
            select(UserChannel).where(
                UserChannel.user_id == uid,
                UserChannel.channel_id == "UC-uncatalogued-channel",
            )
        )
        is None
    )


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
