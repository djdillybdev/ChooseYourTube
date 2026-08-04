from typing import Any, Literal, overload
from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.tag import Tag
from ..models.association_tables import channel_tags, video_tags
from ..tenancy import user_uuid
from .crud_base import (
    base_get,
    _validate_pagination,
    _validate_order_by_field,
)


@overload
async def get_tags(
    db: AsyncSession,
    *,
    owner_id: str | None = None,
    id: str | list[str] | None = None,
    name: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    order_by: str = "name",
    order_direction: Literal["asc", "desc"] = "asc",
    first: Literal[True],
) -> Tag | None: ...


@overload
async def get_tags(
    db: AsyncSession,
    *,
    owner_id: str | None = None,
    id: str | list[str] | None = None,
    name: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    order_by: str = "name",
    order_direction: Literal["asc", "desc"] = "asc",
    first: Literal[False] = False,
) -> list[Tag]: ...


async def get_tags(
    db: AsyncSession,
    *,
    owner_id: str | None = None,
    id: str | list[str] | None = None,
    name: str | None = None,
    # Pagination
    limit: int | None = None,
    offset: int = 0,
    # Ordering
    order_by: str = "name",
    order_direction: Literal["asc", "desc"] = "asc",
    # Return type control
    first: bool = False,
) -> list[Tag] | Tag | None:
    """
    Retrieve tags with flexible filtering, pagination, and ordering.

    Args:
        db: Database session
        id: Single tag ID or list of tag IDs for IN clause
        name: Filter by tag name (case-insensitive)
        limit: Maximum number of results
        offset: Number of results to skip
        order_by: Field to order by (name, created_at, id)
        order_direction: Sort direction ('asc' or 'desc')
        first: If True, return single Tag or None instead of list

    Returns:
        - If first=True: Single Tag instance or None
        - If first=False: List of Tag instances (empty list if no matches)
    """
    _validate_pagination(limit, offset)

    if order_direction not in ("asc", "desc"):
        raise ValueError("order_direction must be 'asc' or 'desc'")

    _validate_order_by_field(Tag, order_by)

    filters: dict[str, Any] = {}
    if owner_id is not None:
        filters["user_id"] = user_uuid(owner_id)
    if id is not None:
        filters["id"] = id
    if name is not None:
        # Normalize to lowercase for case-insensitive search
        filters["name"] = name.lower()

    return await base_get(
        db,
        Tag,
        filters=filters,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_direction=order_direction,
        first=first,
    )


async def count_tags(
    db: AsyncSession,
    *,
    owner_id: str | None = None,
    id: str | list[str] | None = None,
    name: str | None = None,
) -> int:
    """
    Count tags matching the given filters.

    Args:
        db: Database session
        id: Single tag ID or list of tag IDs for IN clause
        name: Filter by tag name (case-insensitive)

    Returns:
        Total count of tags matching the filters
    """
    filters: dict[str, Any] = {}
    if owner_id is not None:
        filters["user_id"] = user_uuid(owner_id)
    if id is not None:
        filters["id"] = id
    if name is not None:
        # Normalize to lowercase for case-insensitive search
        filters["name"] = name.lower()

    # Build the count query
    query = select(func.count()).select_from(Tag)

    # Apply filters
    for field_name, value in filters.items():
        column = getattr(Tag, field_name)
        if isinstance(value, list):
            query = query.where(column.in_(value))
        else:
            query = query.where(column == value)

    result = await db.execute(query)
    return result.scalar() or 0


async def get_tag_usage_counts(
    db: AsyncSession, owner_id: str, tag_ids: list[str]
) -> dict[str, tuple[int, int]]:
    """Return channel and video association counts for each requested tag."""
    if not tag_ids:
        return {}

    channel_rows = await db.execute(
        select(channel_tags.c.tag_id, func.count(channel_tags.c.channel_id))
        .where(
            channel_tags.c.user_id == user_uuid(owner_id),
            channel_tags.c.tag_id.in_(tag_ids),
        )
        .group_by(channel_tags.c.tag_id)
    )
    video_rows = await db.execute(
        select(video_tags.c.tag_id, func.count(video_tags.c.video_id))
        .where(
            video_tags.c.user_id == user_uuid(owner_id),
            video_tags.c.tag_id.in_(tag_ids),
        )
        .group_by(video_tags.c.tag_id)
    )
    channel_counts: dict[str, int] = {
        str(row[0]): int(row[1]) for row in channel_rows.all()
    }
    video_counts: dict[str, int] = {
        str(row[0]): int(row[1]) for row in video_rows.all()
    }
    return {
        tag_id: (channel_counts.get(tag_id, 0), video_counts.get(tag_id, 0))
        for tag_id in tag_ids
    }


async def create_tag(db_session: AsyncSession, tag_to_create: Tag) -> Tag:
    """
    Adds a new Tag instance to the database.
    Tag name will be normalized to lowercase automatically by the Tag model.

    Args:
        db_session: Database session
        tag_to_create: Tag instance to create

    Returns:
        The created Tag instance
    """
    db_session.add(tag_to_create)
    await db_session.commit()
    await db_session.refresh(tag_to_create)
    return tag_to_create


async def get_or_create_tag(
    db_session: AsyncSession, name: str, owner_id: str
) -> Tag:
    """
    Get an existing tag by name, or create it if it doesn't exist.
    This is idempotent - calling it multiple times with the same name returns the same tag.

    Args:
        db_session: Database session
        name: Tag name (will be normalized to lowercase)

    Returns:
        The existing or newly created Tag instance
    """
    # Try to get existing tag (name will be normalized to lowercase in get_tags)
    existing_tag = await get_tags(db_session, owner_id=owner_id, name=name, first=True)

    if existing_tag:
        return existing_tag

    # Create new tag if it doesn't exist
    import uuid

    new_tag = Tag(id=str(uuid.uuid4()), user_id=user_uuid(owner_id), name=name)
    return await create_tag(db_session, new_tag)


async def delete_tag(db_session: AsyncSession, tag: Tag) -> Tag:
    """
    Deletes a tag from the database.

    Args:
        db_session: Database session
        tag: Tag instance to delete

    Returns:
        The deleted Tag instance
    """
    await db_session.delete(tag)
    await db_session.commit()
    return tag


async def delete_all_tags(db_session: AsyncSession, owner_id: str | None = None) -> int:
    """
    Deletes all tags from the database. Used primarily for testing.

    Args:
        db_session: Database session

    Returns:
        Number of tags deleted
    """
    stmt = delete(Tag)
    if owner_id is not None:
        stmt = stmt.where(Tag.user_id == user_uuid(owner_id))
    result = await db_session.execute(stmt)
    await db_session.commit()
    return result.rowcount
