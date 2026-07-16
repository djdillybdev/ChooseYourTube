import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db.crud import crud_category
from ..db.models.category import Category
from ..db.models.channel import Channel
from ..schemas.category import (
    CategoryChannelsUpdate,
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    ChannelCategoriesOut,
    ChannelCategoriesUpdate,
)


def _normalized_name(name: str) -> str:
    return name.casefold()


def _to_out(category: Category) -> CategoryOut:
    return CategoryOut(
        id=category.id,
        name=category.name,
        icon_key=category.icon_key,
        created_at=category.created_at,
        channel_ids=sorted(channel.id for channel in category.channels),
    )


async def list_categories(db: AsyncSession, *, owner_id: str) -> list[CategoryOut]:
    categories = await crud_category.get_categories(db, owner_id=owner_id)
    return [_to_out(category) for category in categories]


async def get_category(
    category_id: str, db: AsyncSession, *, owner_id: str
) -> Category:
    category = await crud_category.get_category(
        db, owner_id=owner_id, category_id=category_id
    )
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


async def get_category_out(
    category_id: str, db: AsyncSession, *, owner_id: str
) -> CategoryOut:
    return _to_out(await get_category(category_id, db, owner_id=owner_id))


async def create_category(
    payload: CategoryCreate, db: AsyncSession, *, owner_id: str
) -> CategoryOut:
    category = Category(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        name=payload.name,
        normalized_name=_normalized_name(payload.name),
        icon_key=payload.icon_key,
    )
    category.channels = []
    try:
        await crud_category.save_category(db, category)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Category name already exists")
    return _to_out(category)


async def update_category(
    category_id: str,
    payload: CategoryUpdate,
    db: AsyncSession,
    *,
    owner_id: str,
) -> CategoryOut:
    category = await get_category(category_id, db, owner_id=owner_id)
    category.name = payload.name
    category.normalized_name = _normalized_name(payload.name)
    if "icon_key" in payload.model_fields_set:
        category.icon_key = payload.icon_key
    try:
        await crud_category.save_category(db, category)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Category name already exists")
    return _to_out(category)


async def delete_category(
    category_id: str, db: AsyncSession, *, owner_id: str
) -> None:
    category = await get_category(category_id, db, owner_id=owner_id)
    await crud_category.delete_category(db, category)


async def _owned_channels(
    db: AsyncSession, owner_id: str, channel_ids: set[str]
) -> list[Channel]:
    if not channel_ids:
        return []
    result = await db.execute(
        select(Channel).where(
            Channel.owner_id == owner_id, Channel.id.in_(channel_ids)
        )
    )
    channels = list(result.scalars().all())
    if {channel.id for channel in channels} != channel_ids:
        raise HTTPException(status_code=400, detail="One or more channels do not exist")
    return channels


async def replace_category_channels(
    category_id: str,
    payload: CategoryChannelsUpdate,
    db: AsyncSession,
    *,
    owner_id: str,
) -> CategoryOut:
    category = await get_category(category_id, db, owner_id=owner_id)
    channels = await _owned_channels(db, owner_id, set(payload.channel_ids))
    category.channels = channels
    await db.commit()
    return _to_out(category)


async def replace_channel_categories(
    channel_id: str,
    payload: ChannelCategoriesUpdate,
    db: AsyncSession,
    *,
    owner_id: str,
) -> ChannelCategoriesOut:
    result = await db.execute(
        select(Channel)
        .where(Channel.owner_id == owner_id, Channel.id == channel_id)
        .options(selectinload(Channel.categories))
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    category_ids = set(payload.category_ids)
    categories: list[Category] = []
    if category_ids:
        category_result = await db.execute(
            select(Category).where(
                Category.owner_id == owner_id, Category.id.in_(category_ids)
            )
        )
        categories = list(category_result.scalars().all())
        if {category.id for category in categories} != category_ids:
            raise HTTPException(
                status_code=400, detail="One or more categories do not exist"
            )

    channel.categories = categories
    await db.commit()
    return ChannelCategoriesOut(
        channel_id=channel.id,
        category_ids=sorted(category.id for category in categories),
    )
