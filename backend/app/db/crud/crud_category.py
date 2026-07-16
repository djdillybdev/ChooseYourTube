from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.category import Category


async def get_categories(db: AsyncSession, *, owner_id: str) -> list[Category]:
    result = await db.execute(
        select(Category)
        .where(Category.owner_id == owner_id)
        .options(selectinload(Category.channels))
        .order_by(func.lower(Category.name), Category.id)
    )
    return list(result.scalars().unique().all())


async def get_category(
    db: AsyncSession, *, owner_id: str, category_id: str
) -> Category | None:
    result = await db.execute(
        select(Category)
        .where(Category.owner_id == owner_id, Category.id == category_id)
        .options(selectinload(Category.channels))
    )
    return result.scalar_one_or_none()


async def save_category(db: AsyncSession, category: Category) -> Category:
    db.add(category)
    await db.commit()
    return category


async def delete_category(db: AsyncSession, category: Category) -> None:
    await db.delete(category)
    await db.commit()
