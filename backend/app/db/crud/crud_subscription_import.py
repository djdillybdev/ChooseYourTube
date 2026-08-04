from __future__ import annotations

import uuid

from sqlalchemy import case, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.subscription_import import (
    SubscriptionImport,
    SubscriptionImportCandidate,
)
from app.db.tenancy import user_uuid


async def get_import(
    db: AsyncSession, import_id: uuid.UUID, *, owner_id: str | None = None
) -> SubscriptionImport | None:
    stmt = select(SubscriptionImport).where(SubscriptionImport.id == import_id)
    if owner_id is not None:
        stmt = stmt.where(SubscriptionImport.user_id == user_uuid(owner_id))
    return await db.scalar(stmt)


async def get_import_by_state_hash(
    db: AsyncSession, state_hash: str, *, for_update: bool = False
) -> SubscriptionImport | None:
    stmt = select(SubscriptionImport).where(
        SubscriptionImport.oauth_state_hash == state_hash
    )
    if for_update:
        stmt = stmt.with_for_update()
    return await db.scalar(stmt)


async def list_candidates(
    db: AsyncSession,
    *,
    import_id: uuid.UUID,
    owner_id: str,
    state: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[SubscriptionImportCandidate], int]:
    stmt = select(SubscriptionImportCandidate).where(
        SubscriptionImportCandidate.import_id == import_id,
    )
    if state is not None:
        stmt = stmt.where(SubscriptionImportCandidate.state == state)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                SubscriptionImportCandidate.channel_title.ilike(pattern),
                SubscriptionImportCandidate.channel_id.ilike(pattern),
            )
        )
    total = int(await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = await db.scalars(
        stmt.order_by(SubscriptionImportCandidate.source_index).limit(limit).offset(offset)
    )
    return list(rows), total


async def get_candidates_by_ids(
    db: AsyncSession,
    *,
    import_id: uuid.UUID,
    owner_id: str,
    candidate_ids: list[uuid.UUID],
) -> list[SubscriptionImportCandidate]:
    if not candidate_ids:
        return []
    rows = await db.scalars(
        select(SubscriptionImportCandidate).where(
            SubscriptionImportCandidate.import_id == import_id,
            SubscriptionImportCandidate.id.in_(candidate_ids),
        )
    )
    return list(rows)


async def candidates_for_processing(
    db: AsyncSession, *, import_id: uuid.UUID, owner_id: str
) -> list[SubscriptionImportCandidate]:
    rows = await db.scalars(
        select(SubscriptionImportCandidate)
        .where(
            SubscriptionImportCandidate.import_id == import_id,
            SubscriptionImportCandidate.state == "selected",
        )
        .order_by(SubscriptionImportCandidate.source_index)
    )
    return list(rows)


async def replace_selection(
    db: AsyncSession,
    *,
    import_id: uuid.UUID,
    owner_id: str,
    selected_ids: list[uuid.UUID],
) -> None:
    await db.execute(
        update(SubscriptionImportCandidate)
        .where(
            SubscriptionImportCandidate.import_id == import_id,
            SubscriptionImportCandidate.state == "selected",
        )
        .values(state="new")
    )
    if selected_ids:
        await db.execute(
            update(SubscriptionImportCandidate)
            .where(
                SubscriptionImportCandidate.import_id == import_id,
                SubscriptionImportCandidate.id.in_(selected_ids),
                SubscriptionImportCandidate.state.in_(("new", "failed")),
            )
            .values(state="selected", message=None)
        )


async def refresh_counts(db: AsyncSession, import_record: SubscriptionImport) -> None:
    row = (
        await db.execute(
            select(
                func.count(SubscriptionImportCandidate.id),
                func.sum(case((SubscriptionImportCandidate.state == "new", 1), else_=0)),
                func.sum(
                    case((SubscriptionImportCandidate.state == "existing", 1), else_=0)
                ),
                func.sum(
                    case((SubscriptionImportCandidate.state == "invalid", 1), else_=0)
                ),
                func.sum(
                    case((SubscriptionImportCandidate.state == "selected", 1), else_=0)
                ),
                func.sum(
                    case((SubscriptionImportCandidate.state == "imported", 1), else_=0)
                ),
                func.sum(
                    case((SubscriptionImportCandidate.state == "failed", 1), else_=0)
                ),
            ).where(
                SubscriptionImportCandidate.import_id == import_record.id,
            )
        )
    ).one()
    (
        import_record.candidate_count,
        import_record.new_count,
        import_record.existing_count,
        import_record.invalid_count,
        import_record.selected_count,
        import_record.imported_count,
        import_record.failed_count,
    ) = tuple(int(value or 0) for value in row)
