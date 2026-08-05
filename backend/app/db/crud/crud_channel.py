from typing import Literal, overload

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.association_tables import channel_categories, channel_tags, playlist_videos, video_tags
from ..models.channel import Channel
from ..models.tag import Tag
from ..models.user_state import UserChannel
from ..models.user_state import UserVideoState
from ..models.video import Video
from ..tenancy import user_uuid
from .crud_base import _validate_order_by_field, _validate_pagination

_UNSET = object()


async def _decorate(db: AsyncSession, rows: list[tuple[Channel, UserChannel]]) -> list[Channel]:
    if not rows:
        return []
    uid = rows[0][1].user_id
    ids = [channel.id for channel, _ in rows]
    tag_rows = await db.execute(
        select(channel_tags.c.channel_id, Tag)
        .join(Tag, (Tag.user_id == channel_tags.c.user_id) & (Tag.id == channel_tags.c.tag_id))
        .where(channel_tags.c.user_id == uid, channel_tags.c.channel_id.in_(ids))
    )
    tags: dict[str, list[Tag]] = {channel_id: [] for channel_id in ids}
    for channel_id, tag in tag_rows.all():
        tags[channel_id].append(tag)
    decorated: list[Channel] = []
    for channel, link in rows:
        channel.is_favorited = link.is_favorited
        channel.folder_id = link.folder_id
        channel.followed_at = link.followed_at
        channel.tags = tags[channel.id]
        channel.tag_ids = [tag.id for tag in tags[channel.id]]
        channel.user_link = link
        decorated.append(channel)
    return decorated


@overload
async def get_channels(
    db: AsyncSession, *, owner_id: str, first: Literal[True], **kwargs
) -> Channel | None: ...


@overload
async def get_channels(
    db: AsyncSession, *, owner_id: str, first: Literal[False] = False, **kwargs
) -> list[Channel]: ...


async def get_channels(
    db: AsyncSession,
    *,
    owner_id: str,
    id: str | list[str] | None = None,
    title: str | None = None,
    handle: str | None = None,
    description: str | None = None,
    is_favorited: bool | None = None,
    folder_id: str | list[str] | None | object = _UNSET,
    limit: int | None = None,
    offset: int = 0,
    order_by: str = "title",
    order_direction: Literal["asc", "desc"] = "asc",
    first: bool = False,
    **kwargs,
) -> list[Channel] | Channel | None:
    _validate_pagination(limit, offset)
    if order_direction not in ("asc", "desc"):
        raise ValueError("order_direction must be 'asc' or 'desc'")
    _validate_order_by_field(Channel, order_by)
    if isinstance(id, list) and not id:
        raise ValueError("id filter list cannot be empty")
    if isinstance(folder_id, list) and not folder_id:
        raise ValueError("folder_id filter list cannot be empty")

    uid = user_uuid(owner_id)
    query = select(Channel, UserChannel).join(
        UserChannel,
        (UserChannel.channel_id == Channel.id) & (UserChannel.user_id == uid),
    )
    if id is not None:
        query = query.where(Channel.id.in_(id) if isinstance(id, list) else Channel.id == id)
    if title is not None:
        query = query.where(Channel.title == title)
    if handle is not None:
        query = query.where(Channel.handle == handle)
    if description is not None:
        query = query.where(Channel.description == description)
    if is_favorited is not None:
        query = query.where(UserChannel.is_favorited == is_favorited)
    if folder_id is not _UNSET:
        if isinstance(folder_id, list):
            query = query.where(UserChannel.folder_id.in_(folder_id))
        elif folder_id is None:
            query = query.where(UserChannel.folder_id.is_(None))
        else:
            query = query.where(UserChannel.folder_id == folder_id)
    order_column = UserChannel.followed_at if order_by == "created_at" else getattr(Channel, order_by)
    query = query.order_by(order_column.desc() if order_direction == "desc" else order_column.asc())
    if limit is not None:
        query = query.limit(limit)
    query = query.offset(offset)
    result = await db.execute(query)
    decorated = await _decorate(db, [(row[0], row[1]) for row in result.all()])
    return (decorated[0] if decorated else None) if first else decorated


async def create_channel(db_session: AsyncSession, channel_to_create: Channel) -> Channel:
    db_session.add(channel_to_create)
    await db_session.commit()
    await db_session.refresh(channel_to_create)
    return channel_to_create


async def update_channel(db_session: AsyncSession, channel: Channel) -> Channel:
    await db_session.commit()
    return channel


async def delete_channel(db_session: AsyncSession, channel_to_delete: Channel, owner_id: str) -> None:
    uid = user_uuid(owner_id)
    # Serialize follow/unfollow and catalog garbage collection for this channel.
    locked_channel = await db_session.scalar(
        select(Channel)
        .where(Channel.id == channel_to_delete.id)
        .with_for_update()
    )
    if locked_channel is None:
        return
    video_ids = select(Video.id).where(Video.channel_id == channel_to_delete.id)
    await db_session.execute(delete(channel_categories).where(
        channel_categories.c.user_id == uid,
        channel_categories.c.channel_id == channel_to_delete.id,
    ))
    await db_session.execute(delete(channel_tags).where(
        channel_tags.c.user_id == uid,
        channel_tags.c.channel_id == channel_to_delete.id,
    ))
    await db_session.execute(delete(UserVideoState).where(
        UserVideoState.user_id == uid, UserVideoState.video_id.in_(video_ids)
    ))
    await db_session.execute(delete(video_tags).where(
        video_tags.c.user_id == uid, video_tags.c.video_id.in_(video_ids)
    ))
    await db_session.execute(delete(playlist_videos).where(
        playlist_videos.c.user_id == uid, playlist_videos.c.video_id.in_(video_ids)
    ))
    await db_session.execute(
        delete(UserChannel).where(UserChannel.user_id == uid, UserChannel.channel_id == channel_to_delete.id)
    )
    remaining = await db_session.scalar(
        select(UserChannel.channel_id).where(UserChannel.channel_id == channel_to_delete.id).limit(1)
    )
    if remaining is None:
        await db_session.delete(locked_channel)
    await db_session.commit()


async def delete_all_channels(db_session: AsyncSession, owner_id: str) -> int:
    channels = await get_channels(db_session, owner_id=owner_id)
    for channel in list(channels):
        await delete_channel(db_session, channel, owner_id)
    return len(channels)
