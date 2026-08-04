from datetime import datetime
from typing import Any, Literal, overload

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.association_tables import video_tags
from ..models.tag import Tag
from ..models.user_state import UserChannel, UserVideoState
from ..models.video import Video
from ..tenancy import user_uuid
from ...schemas.video import VideoCreate

RELEVANCE_ORDER_BY = "relevance"


def _dialect(db: AsyncSession) -> str | None:
    return getattr(getattr(getattr(db, "bind", None), "dialect", None), "name", None)


async def create_videos_bulk(db: AsyncSession, videos: list[VideoCreate]) -> None:
    if not videos:
        return
    values = [item.model_dump(exclude={"owner_id"}) for item in videos]
    statement: Any
    if _dialect(db) == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        statement = sqlite_insert(Video).values(values).on_conflict_do_nothing(index_elements=["id"])
    else:
        from sqlalchemy.dialects.postgresql import insert as postgresql_insert

        statement = postgresql_insert(Video).values(values).on_conflict_do_nothing(index_elements=["id"])
    await db.execute(statement)
    await db.commit()


def _base_query(owner_id: str):
    uid = user_uuid(owner_id)
    return (
        select(Video, UserVideoState)
        .join(UserChannel, (UserChannel.channel_id == Video.channel_id) & (UserChannel.user_id == uid))
        .outerjoin(UserVideoState, (UserVideoState.video_id == Video.id) & (UserVideoState.user_id == uid))
    ), uid


def _apply_filters(
    query,
    *,
    uid,
    id=None,
    channel_id=None,
    is_favorited=None,
    is_short=None,
    is_watched=None,
    tag_id=None,
    published_after=None,
    published_before=None,
    min_duration_seconds=None,
    max_duration_seconds=None,
    q=None,
):
    if id is not None:
        query = query.where(Video.id.in_(id) if isinstance(id, list) else Video.id == id)
    if channel_id is not None:
        query = query.where(Video.channel_id.in_(channel_id) if isinstance(channel_id, list) else Video.channel_id == channel_id)
    if is_short is not None:
        query = query.where(Video.is_short == is_short)
    favorite = func.coalesce(UserVideoState.is_favorited, False)
    watched = func.coalesce(UserVideoState.is_watched, False)
    if is_favorited is not None:
        query = query.where(favorite == is_favorited)
    if is_watched is not None:
        query = query.where(watched == is_watched)
    if tag_id is not None:
        query = query.join(
            video_tags,
            (video_tags.c.user_id == uid) & (video_tags.c.video_id == Video.id),
        ).where(video_tags.c.tag_id == tag_id)
    if published_after is not None:
        query = query.where(Video.published_at >= published_after)
    if published_before is not None:
        query = query.where(Video.published_at <= published_before)
    if min_duration_seconds is not None:
        query = query.where(Video.duration_seconds >= min_duration_seconds)
    if max_duration_seconds is not None:
        query = query.where(Video.duration_seconds <= max_duration_seconds)
    if q and q.strip():
        pattern = f"%{q.strip().lower()}%"
        tagged = select(video_tags.c.video_id).join(
            Tag,
            (Tag.user_id == video_tags.c.user_id) & (Tag.id == video_tags.c.tag_id),
        ).where(video_tags.c.user_id == uid, func.lower(Tag.name).like(pattern))
        query = query.where(
            or_(
                func.lower(Video.title).like(pattern),
                func.lower(func.coalesce(Video.description, "")).like(pattern),
                Video.id.in_(tagged),
            )
        )
    return query


async def _decorate(db: AsyncSession, uid, rows) -> list[Video]:
    pairs = list(rows)
    if not pairs:
        return []
    ids = [video.id for video, _ in pairs]
    result = await db.execute(
        select(video_tags.c.video_id, Tag)
        .join(Tag, (Tag.user_id == video_tags.c.user_id) & (Tag.id == video_tags.c.tag_id))
        .where(video_tags.c.user_id == uid, video_tags.c.video_id.in_(ids))
    )
    tags: dict[str, list[Tag]] = {video_id: [] for video_id in ids}
    for video_id, tag in result.all():
        tags[video_id].append(tag)
    output = []
    for video, state in pairs:
        video.is_favorited = state.is_favorited if state else False
        video.is_watched = state.is_watched if state else False
        video.user_state = state
        video.tags = tags[video.id]
        video.tag_ids = [tag.id for tag in tags[video.id]]
        output.append(video)
    return output


@overload
async def get_videos(
    db: AsyncSession, *, owner_id: str, first: Literal[True], **kwargs: Any
) -> Video | None: ...


@overload
async def get_videos(
    db: AsyncSession, *, owner_id: str, first: Literal[False] = False, **kwargs: Any
) -> list[Video]: ...


async def get_videos(
    db: AsyncSession,
    *,
    owner_id: str,
    id: str | list[str] | None = None,
    channel_id: str | list[str] | None = None,
    is_favorited: bool | None = None,
    is_short: bool | None = None,
    is_watched: bool | None = None,
    tag_id: str | None = None,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
    min_duration_seconds: int | None = None,
    max_duration_seconds: int | None = None,
    q: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    order_by: str = "published_at",
    order_direction: Literal["asc", "desc"] = "desc",
    first: bool = False,
    **kwargs: Any,
) -> list[Video] | Video | None:
    query, uid = _base_query(owner_id)
    query = _apply_filters(
        query, uid=uid, id=id, channel_id=channel_id, is_favorited=is_favorited,
        is_short=is_short, is_watched=is_watched, tag_id=tag_id,
        published_after=published_after, published_before=published_before,
        min_duration_seconds=min_duration_seconds, max_duration_seconds=max_duration_seconds, q=q,
    )
    effective_order = "published_at" if order_by == RELEVANCE_ORDER_BY else order_by
    column = getattr(Video, effective_order)
    query = query.order_by(column.desc().nullslast() if order_direction == "desc" else column.asc())
    if limit is not None:
        query = query.limit(limit)
    query = query.offset(offset)
    result = await db.execute(query)
    videos = await _decorate(db, uid, result.unique().all())
    return (videos[0] if videos else None) if first else videos


async def count_videos(db: AsyncSession, *, owner_id: str, **filters: Any) -> int:
    query, uid = _base_query(owner_id)
    query = _apply_filters(query, uid=uid, **filters)
    subquery = query.with_only_columns(Video.id).distinct().subquery()
    return int((await db.scalar(select(func.count()).select_from(subquery))) or 0)


async def update_video(db: AsyncSession, video: Video) -> Video:
    await db.commit()
    return video


async def delete_video(db: AsyncSession, video: Video) -> None:
    await db.delete(video)
    await db.commit()
