import uuid

import pytest
from sqlalchemy import select

from app.auth.models import User
from app.db.crud import crud_channel, crud_video
from app.db.models.channel import Channel
from app.db.models.user_state import UserChannel, UserVideoState
from app.db.models.video import Video
from app.schemas.channel import ChannelUpdate
from app.schemas.video import VideoUpdate
from app.services import channel_service, video_service
from app.services import playlist_service


@pytest.mark.asyncio
async def test_shared_catalog_keeps_personal_channel_and_video_state_isolated(db_session):
    first_id = uuid.UUID("10000000-0000-0000-0000-000000000001")
    second_id = uuid.UUID("10000000-0000-0000-0000-000000000002")
    db_session.add_all(
        [
            User(id=first_id, email="first@example.com", hashed_password="hash"),
            User(id=second_id, email="second@example.com", hashed_password="hash"),
            Channel(id="shared-channel", title="Shared", handle="shared", uploads_playlist_id="uploads"),
        ]
    )
    await db_session.flush()
    db_session.add_all(
        [
            UserChannel(user_id=first_id, channel_id="shared-channel"),
            UserChannel(user_id=second_id, channel_id="shared-channel"),
            Video(id="shared-video", channel_id="shared-channel", title="Video", is_short=False),
        ]
    )
    await db_session.commit()

    await channel_service.update_channel(
        "shared-channel", ChannelUpdate(is_favorited=True), db_session, owner_id=str(first_id)
    )
    await video_service.update_video(
        "shared-video", VideoUpdate(is_watched=True), db_session, owner_id=str(first_id)
    )

    first_channel = await crud_channel.get_channels(
        db_session, owner_id=str(first_id), id="shared-channel", first=True
    )
    assert first_channel is not None and first_channel.is_favorited is True
    second_channel = await crud_channel.get_channels(
        db_session, owner_id=str(second_id), id="shared-channel", first=True
    )
    assert second_channel is not None and second_channel.is_favorited is False
    first_video = await crud_video.get_videos(
        db_session, owner_id=str(first_id), id="shared-video", first=True
    )
    assert first_video is not None and first_video.is_watched is True
    second_video = await crud_video.get_videos(
        db_session, owner_id=str(second_id), id="shared-video", first=True
    )

    assert second_video is not None and second_video.is_watched is False
    assert await db_session.scalar(select(UserVideoState).where(
        UserVideoState.user_id == first_id, UserVideoState.video_id == "shared-video"
    )) is not None


@pytest.mark.asyncio
async def test_unfollow_removes_only_personal_state_and_last_unfollow_removes_catalog(db_session):
    first_id = uuid.UUID("20000000-0000-0000-0000-000000000001")
    second_id = uuid.UUID("20000000-0000-0000-0000-000000000002")
    db_session.add_all(
        [
            User(id=first_id, email="first-delete@example.com", hashed_password="hash"),
            User(id=second_id, email="second-delete@example.com", hashed_password="hash"),
            Channel(id="delete-channel", title="Shared", handle="delete", uploads_playlist_id="uploads"),
        ]
    )
    await db_session.flush()
    db_session.add_all(
        [
            UserChannel(user_id=first_id, channel_id="delete-channel"),
            UserChannel(user_id=second_id, channel_id="delete-channel"),
            Video(id="delete-video", channel_id="delete-channel", title="Video", is_short=False),
        ]
    )
    await db_session.flush()
    db_session.add(UserVideoState(user_id=first_id, video_id="delete-video", is_watched=True))
    await db_session.commit()

    channel = await crud_channel.get_channels(
        db_session, owner_id=str(first_id), id="delete-channel", first=True
    )
    assert channel is not None
    await crud_channel.delete_channel(db_session, channel, str(first_id))
    assert await db_session.get(Channel, "delete-channel") is not None
    assert await db_session.get(Video, "delete-video") is not None
    assert await db_session.get(UserVideoState, (first_id, "delete-video")) is None

    channel = await crud_channel.get_channels(
        db_session, owner_id=str(second_id), id="delete-channel", first=True
    )
    assert channel is not None
    await crud_channel.delete_channel(db_session, channel, str(second_id))
    assert await db_session.get(Channel, "delete-channel") is None


@pytest.mark.asyncio
async def test_watch_later_membership_is_owned_and_uses_shared_video(db_session):
    user_id = uuid.UUID("30000000-0000-0000-0000-000000000001")
    db_session.add_all(
        [
            User(id=user_id, email="playlist@example.com", hashed_password="hash"),
            Channel(id="playlist-channel", title="Shared", handle="playlist", uploads_playlist_id="uploads"),
        ]
    )
    await db_session.flush()
    db_session.add_all(
        [
            UserChannel(user_id=user_id, channel_id="playlist-channel"),
            Video(id="playlist-video", channel_id="playlist-channel", title="Video", is_short=False),
        ]
    )
    await db_session.commit()

    detail = await playlist_service.add_video_to_watch_later(
        "playlist-video", db_session, owner_id=str(user_id)
    )
    assert detail.video_ids == ["playlist-video"]
    assert detail.system_key == "watch_later"


@pytest.mark.asyncio
async def test_unfollowed_catalog_is_invisible_and_empty_video_state_is_sparse(db_session):
    follower_id = uuid.UUID("40000000-0000-0000-0000-000000000001")
    outsider_id = uuid.UUID("40000000-0000-0000-0000-000000000002")
    db_session.add_all(
        [
            User(id=follower_id, email="follower@example.com", hashed_password="hash"),
            User(id=outsider_id, email="outsider@example.com", hashed_password="hash"),
            Channel(
                id="private-library-channel",
                title="Catalog entry",
                handle="catalog-entry",
                uploads_playlist_id="uploads",
            ),
        ]
    )
    await db_session.flush()
    db_session.add_all(
        [
            UserChannel(user_id=follower_id, channel_id="private-library-channel"),
            Video(
                id="private-video",
                channel_id="private-library-channel",
                title="Video",
                is_short=False,
            ),
        ]
    )
    await db_session.commit()

    assert await crud_channel.get_channels(
        db_session, owner_id=str(outsider_id), id="private-library-channel", first=True
    ) is None
    assert await crud_video.get_videos(
        db_session, owner_id=str(outsider_id), id="private-video", first=True
    ) is None

    await video_service.update_video(
        "private-video",
        VideoUpdate(is_favorited=True, is_watched=True),
        db_session,
        owner_id=str(follower_id),
    )
    await video_service.update_video(
        "private-video",
        VideoUpdate(is_favorited=False, is_watched=False),
        db_session,
        owner_id=str(follower_id),
    )
    assert await db_session.get(UserVideoState, (follower_id, "private-video")) is None
