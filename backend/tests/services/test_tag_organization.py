from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.db.models.channel import Channel
from app.db.models.tag import Tag
from app.db.models.video import Video
from app.schemas.tag import TagCreate, TagUpdate
from app.services.channel_service import update_channel
from app.services.tag_service import get_all_tags
from app.services.video_service import update_video
from app.schemas.channel import ChannelUpdate
from app.schemas.video import VideoUpdate

TEST_OWNER_ID = "10000000-0000-0000-0000-000000000099"


def test_tag_names_normalize_and_reject_whitespace():
    assert TagCreate(name="  Portfolio  ").name == "portfolio"
    assert TagUpdate(name="  DEV ").name == "dev"
    with pytest.raises(ValidationError):
        TagCreate(name="   ")


@pytest.mark.asyncio
async def test_tag_list_includes_channel_and_video_usage_counts(db_session):
    tag = Tag(id="tag-counts", owner_id=TEST_OWNER_ID, name="counted")
    channel = Channel(
        id="CH_tag_counts",
        owner_id=TEST_OWNER_ID,
        title="Tagged channel",
        handle="tagcounts",
        uploads_playlist_id="UU_tag_counts",
    )
    video = Video(
        id="TAGVIDEO01",
        owner_id=TEST_OWNER_ID,
        channel_id=channel.id,
        title="Tagged video",
        published_at=datetime.now(timezone.utc),
        duration_seconds=60,
    )
    db_session.add_all([tag, channel, video])
    await db_session.commit()

    await update_channel(
        channel.id,
        ChannelUpdate(tag_ids=[tag.id]),
        db_session,
        owner_id=TEST_OWNER_ID,
    )
    await update_video(
        video.id, VideoUpdate(tag_ids=[tag.id]), db_session, owner_id=TEST_OWNER_ID
    )

    response = await get_all_tags(db_session, owner_id=TEST_OWNER_ID)
    assert response.items[0].channel_count == 1
    assert response.items[0].video_count == 1
