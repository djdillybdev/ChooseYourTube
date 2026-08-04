"""
Tag management service.

Provides utilities for tag synchronization and management across entities.
"""

import uuid
from typing import Protocol, cast
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import delete, insert

from app.schemas.base import PaginatedResponse

from ..db.crud import crud_tag
from ..db.models.tag import Tag
from ..db.models.channel import Channel
from ..db.models.association_tables import channel_tags, video_tags
from ..db.tenancy import user_uuid
from ..db.crud import crud_channel, crud_video
from sqlalchemy import select
from ..schemas.tag import TagCreate, TagUpdate, TagOut


class TaggableEntity(Protocol):
    """Protocol for entities that can have tags."""

    tags: list  # Relationship to Tag model
    id: str
    tag_ids: list[str]


async def _serialize_tags_with_counts(
    tags: list[Tag], db_session: AsyncSession, owner_id: str
) -> list[TagOut]:
    counts = await crud_tag.get_tag_usage_counts(
        db_session, owner_id, [tag.id for tag in tags]
    )
    return [
        TagOut(
            id=tag.id,
            name=tag.name,
            created_at=tag.created_at,
            channel_count=counts.get(tag.id, (0, 0))[0],
            video_count=counts.get(tag.id, (0, 0))[1],
        )
        for tag in tags
    ]


async def sync_entity_tags(
    entity: TaggableEntity,
    tag_ids: list[str],
    db_session: AsyncSession,
    owner_id: str,
) -> None:
    """
    Synchronize tags for any entity (Channel or Video).

    This function handles the complete tag synchronization:
    1. Validates all requested tags exist in database
    2. Calculates which tags to add and remove
    3. Updates the entity's tag relationships

    Args:
        entity: The entity (Channel or Video) to sync tags for
        tag_ids: List of tag IDs that should be associated with the entity
        db_session: Database session for queries

    Raises:
        HTTPException: If any requested tag ID doesn't exist
    """
    from ..db.models.tag import Tag

    # Load all requested tags from database
    requested_tag_ids = set(tag_ids)
    uid = user_uuid(owner_id)
    requested_tags = []

    for tag_id in requested_tag_ids:
        tag = await db_session.get(Tag, tag_id)
        if tag is None or tag.user_id != uid:
            raise HTTPException(
                status_code=400, detail=f"Tag with id {tag_id} does not exist"
            )
        requested_tags.append(tag)

    table = channel_tags if isinstance(entity, Channel) else video_tags
    entity_column = table.c.channel_id if isinstance(entity, Channel) else table.c.video_id
    await db_session.execute(
        delete(table).where(table.c.user_id == uid, entity_column == entity.id)
    )
    for tag in requested_tags:
        await db_session.execute(
            insert(table).values(user_id=uid, **{entity_column.key: entity.id}, tag_id=tag.id)
        )
    entity.tags = requested_tags
    entity.tag_ids = [tag.id for tag in requested_tags]


async def get_all_tags(
    db_session: AsyncSession,
    owner_id: str,
    limit: int = 50,
    offset: int = 0,
) -> PaginatedResponse[TagOut]:
    """
    Get all tags with pagination.

    Args:
        db_session: Database session
        limit: Maximum number of tags to return
        offset: Number of tags to skip

    Returns:
        List of Tag instances
    """
    # Get total count before pagination
    total = await crud_tag.count_tags(db_session, owner_id=owner_id)

    tags = await crud_tag.get_tags(
        db_session,
        owner_id=owner_id,
        limit=limit,
        offset=offset,
        order_by="name",
        order_direction="asc",
    )

    serialized = await _serialize_tags_with_counts(
        cast(list[Tag], tags), db_session, owner_id
    )
    return PaginatedResponse[TagOut](
        total=total,
        items=serialized,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total if limit else False,
    )


async def get_tag_by_id(
    tag_id: str, db_session: AsyncSession, owner_id: str
) -> Tag:
    """
    Get a tag by its ID.

    Args:
        tag_id: Tag ID
        db_session: Database session

    Returns:
        Tag instance

    Raises:
        HTTPException: If tag not found
    """
    tag = await crud_tag.get_tags(db_session, owner_id=owner_id, id=tag_id, first=True)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


async def get_tag_out_by_id(
    tag_id: str, db_session: AsyncSession, owner_id: str
) -> TagOut:
    tag = await get_tag_by_id(tag_id, db_session, owner_id=owner_id)
    return (await _serialize_tags_with_counts([tag], db_session, owner_id))[0]


async def create_new_tag(
    payload: TagCreate, db_session: AsyncSession, owner_id: str
) -> Tag:
    """
    Create a new tag.

    Args:
        payload: Tag creation data
        db_session: Database session

    Returns:
        Created Tag instance

    Raises:
        HTTPException: If tag with same name already exists
    """
    # Check if tag with this name already exists
    existing_tag = await crud_tag.get_tags(
        db_session, owner_id=owner_id, name=payload.name, first=True
    )
    if existing_tag:
        raise HTTPException(
            status_code=409, detail=f"Tag with name '{payload.name}' already exists"
        )

    # Generate UUID for new tag
    tag_id = str(uuid.uuid4())
    new_tag = Tag(id=tag_id, user_id=user_uuid(owner_id), name=payload.name)
    try:
        return await crud_tag.create_tag(db_session, new_tag)
    except IntegrityError:
        await db_session.rollback()
        raise HTTPException(
            status_code=409, detail=f"Tag with name '{payload.name}' already exists"
        )


async def update_tag(
    tag_id: str,
    payload: TagUpdate,
    db_session: AsyncSession,
    owner_id: str,
) -> TagOut:
    """
    Update a tag's name.

    Args:
        tag_id: Tag ID
        payload: Update data
        db_session: Database session

    Returns:
        Updated Tag instance

    Raises:
        HTTPException: If tag not found or new name conflicts with existing tag
    """
    # Get existing tag
    tag = await get_tag_by_id(tag_id, db_session, owner_id=owner_id)

    # Update name if provided
    if payload.name is not None:
        # Check if new name conflicts with existing tag
        existing_tag = await crud_tag.get_tags(
            db_session, owner_id=owner_id, name=payload.name, first=True
        )
        if existing_tag and existing_tag.id != tag_id:
            raise HTTPException(
                status_code=409, detail=f"Tag with name '{payload.name}' already exists"
            )
        tag.name = payload.name

    # Save changes
    db_session.add(tag)
    await db_session.commit()
    await db_session.refresh(tag)
    return (await _serialize_tags_with_counts([tag], db_session, owner_id))[0]


async def delete_tag_by_id(
    tag_id: str, db_session: AsyncSession, owner_id: str
) -> None:
    """
    Delete a tag by its ID.

    Args:
        tag_id: Tag ID
        db_session: Database session

    Raises:
        HTTPException: If tag not found
    """
    # Get tag to ensure it exists
    tag = await get_tag_by_id(tag_id, db_session, owner_id=owner_id)

    # Delete the tag (relationships will be cleaned up automatically)
    await crud_tag.delete_tag(db_session, tag)


async def get_videos_for_tag(
    tag_id: str,
    db_session: AsyncSession,
    owner_id: str,
    limit: int = 50,
    offset: int = 0,
):
    """
    Get all videos associated with a tag.

    Args:
        tag_id: Tag ID
        db_session: Database session
        limit: Maximum number of videos to return
        offset: Number of videos to skip

    Returns:
        List of Video instances

    Raises:
        HTTPException: If tag not found
    """
    # Get tag with videos relationship
    await get_tag_by_id(tag_id, db_session, owner_id=owner_id)
    return await crud_video.get_videos(
        db_session, owner_id=owner_id, tag_id=tag_id, limit=limit, offset=offset
    )


async def get_channels_for_tag(
    tag_id: str,
    db_session: AsyncSession,
    owner_id: str,
    limit: int = 50,
    offset: int = 0,
):
    """
    Get all channels associated with a tag.

    Args:
        tag_id: Tag ID
        db_session: Database session
        limit: Maximum number of channels to return
        offset: Number of channels to skip

    Returns:
        List of Channel instances

    Raises:
        HTTPException: If tag not found
    """
    # Get tag with channels relationship
    await get_tag_by_id(tag_id, db_session, owner_id=owner_id)
    uid = user_uuid(owner_id)
    ids = list((await db_session.scalars(
        select(channel_tags.c.channel_id).where(
            channel_tags.c.user_id == uid, channel_tags.c.tag_id == tag_id
        )
    )).all())
    return await crud_channel.get_channels(
        db_session, owner_id=owner_id, id=ids, limit=limit, offset=offset
    )
