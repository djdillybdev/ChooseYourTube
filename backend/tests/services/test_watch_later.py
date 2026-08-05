from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.db.models.channel import Channel
from app.db.models.video import Video
from app.schemas.playlist import PlaylistUpdate
from app.services.playlist_service import (
    add_video_to_watch_later as _add_video_to_watch_later,
    delete_playlist_by_id as _delete_playlist_by_id,
    ensure_watch_later as _ensure_watch_later,
    get_watch_later_detail as _get_watch_later_detail,
    remove_video_from_watch_later as _remove_video_from_watch_later,
    update_playlist as _update_playlist,
)

TEST_OWNER_ID = "10000000-0000-0000-0000-000000000099"
OTHER_OWNER_ID = "20000000-0000-0000-0000-000000000099"


def _owned_service(function):
    async def call(*args, **kwargs):
        owner_id = kwargs.get("owner_id", TEST_OWNER_ID)
        kwargs["owner_id"] = (
            OTHER_OWNER_ID if owner_id == "other-owner" else owner_id
        )
        return await function(*args, **kwargs)

    return call


add_video_to_watch_later = _owned_service(_add_video_to_watch_later)
delete_playlist_by_id = _owned_service(_delete_playlist_by_id)
ensure_watch_later = _owned_service(_ensure_watch_later)
get_watch_later_detail = _owned_service(_get_watch_later_detail)
remove_video_from_watch_later = _owned_service(_remove_video_from_watch_later)
update_playlist = _owned_service(_update_playlist)


@pytest.fixture
async def watch_later_video(db_session):
    channel = Channel(
        id="CH_watch_later",
        owner_id=TEST_OWNER_ID,
        title="Watch Later Channel",
        handle="watchlater",
        uploads_playlist_id="UU_watch_later",
    )
    video = Video(
        id="WLVIDEO001",
        owner_id=TEST_OWNER_ID,
        channel_id=channel.id,
        title="Saved video",
        published_at=datetime.now(timezone.utc),
        duration_seconds=120,
    )
    db_session.add_all([channel, video])
    await db_session.commit()
    return video


@pytest.mark.asyncio
async def test_ensure_watch_later_is_idempotent(db_session):
    first = await ensure_watch_later(db_session)
    second = await ensure_watch_later(db_session)

    assert first.id == second.id
    assert first.system_key == "watch_later"
    assert first.is_system is True
    assert first.source_type == "manual"


@pytest.mark.asyncio
async def test_add_and_remove_are_idempotent(db_session, watch_later_video):
    first = await add_video_to_watch_later(watch_later_video.id, db_session)
    second = await add_video_to_watch_later(watch_later_video.id, db_session)

    assert first.video_ids == [watch_later_video.id]
    assert second.video_ids == [watch_later_video.id]

    await remove_video_from_watch_later(watch_later_video.id, db_session)
    await remove_video_from_watch_later(watch_later_video.id, db_session)
    detail = await get_watch_later_detail(db_session)
    assert detail.video_ids == []


@pytest.mark.asyncio
async def test_add_rejects_missing_or_other_owner_video(db_session, watch_later_video):
    with pytest.raises(HTTPException) as missing:
        await add_video_to_watch_later("missing", db_session)
    assert missing.value.status_code == 404

    with pytest.raises(HTTPException) as other_owner:
        await add_video_to_watch_later(
            watch_later_video.id, db_session, owner_id="other-owner"
        )
    assert other_owner.value.status_code == 404


@pytest.mark.asyncio
async def test_watch_later_cannot_be_renamed_or_deleted(db_session):
    playlist = await ensure_watch_later(db_session)

    with pytest.raises(HTTPException) as update_error:
        await update_playlist(
            playlist.id, PlaylistUpdate(name="Renamed"), db_session
        )
    assert update_error.value.status_code == 403

    with pytest.raises(HTTPException) as delete_error:
        await delete_playlist_by_id(playlist.id, db_session)
    assert delete_error.value.status_code == 403
