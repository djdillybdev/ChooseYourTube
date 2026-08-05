from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.association_tables import channel_categories
from ..models.category import Category
from ..models.channel import Channel
from ..tenancy import user_uuid


async def _decorate(db: AsyncSession, user_id, categories: list[Category]) -> list[Category]:
    if not categories:
        return categories
    rows = await db.execute(
        select(channel_categories.c.category_id, Channel)
        .join(Channel, Channel.id == channel_categories.c.channel_id)
        .where(
            channel_categories.c.user_id == user_id,
            channel_categories.c.category_id.in_([category.id for category in categories]),
        )
    )
    grouped: dict[str, list[Channel]] = {category.id: [] for category in categories}
    for category_id, channel in rows.all():
        grouped[category_id].append(channel)
    for category in categories:
        category.channels = grouped[category.id]
    return categories


async def get_categories(db: AsyncSession, *, owner_id: str) -> list[Category]:
    uid = user_uuid(owner_id)
    result = await db.execute(
        select(Category).where(Category.user_id == uid).order_by(func.lower(Category.name), Category.id)
    )
    return await _decorate(db, uid, list(result.scalars().all()))


async def get_category(db: AsyncSession, *, owner_id: str, category_id: str) -> Category | None:
    uid = user_uuid(owner_id)
    category = await db.scalar(
        select(Category).where(Category.user_id == uid, Category.id == category_id)
    )
    if category is not None:
        await _decorate(db, uid, [category])
    return category


async def save_category(db: AsyncSession, category: Category) -> Category:
    db.add(category)
    await db.commit()
    return category


async def delete_category(db: AsyncSession, category: Category) -> None:
    await db.delete(category)
    await db.commit()
