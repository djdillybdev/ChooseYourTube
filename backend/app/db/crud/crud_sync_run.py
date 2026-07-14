from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.sync_run import SyncRun, YouTubeAPIUsage


async def get_sync_run(
    db: AsyncSession, sync_run_id: uuid.UUID, *, owner_id: str | None = None
) -> SyncRun | None:
    stmt = select(SyncRun).where(SyncRun.id == sync_run_id)
    if owner_id is not None:
        stmt = stmt.where(SyncRun.owner_id == owner_id)
    return await db.scalar(stmt)


async def get_active_sync_run(
    db: AsyncSession, *, owner_id: str, channel_id: str, kind: str
) -> SyncRun | None:
    return await db.scalar(
        select(SyncRun)
        .where(
            SyncRun.owner_id == owner_id,
            SyncRun.channel_id == channel_id,
            SyncRun.kind == kind,
            SyncRun.status.in_(("queued", "running")),
        )
        .order_by(SyncRun.queued_at.desc())
        .limit(1)
    )


def _filtered_runs_query(
    *, owner_id: str, status: str | None, kind: str | None, channel_id: str | None
) -> Select[tuple[SyncRun]]:
    stmt = select(SyncRun).where(SyncRun.owner_id == owner_id)
    if status is not None:
        stmt = stmt.where(SyncRun.status == status)
    if kind is not None:
        stmt = stmt.where(SyncRun.kind == kind)
    if channel_id is not None:
        stmt = stmt.where(SyncRun.channel_id == channel_id)
    return stmt


async def list_sync_runs(
    db: AsyncSession,
    *,
    owner_id: str,
    status: str | None = None,
    kind: str | None = None,
    channel_id: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[SyncRun], int]:
    filtered = _filtered_runs_query(
        owner_id=owner_id, status=status, kind=kind, channel_id=channel_id
    )
    total = int(
        await db.scalar(select(func.count()).select_from(filtered.subquery())) or 0
    )
    rows = await db.scalars(
        filtered.order_by(SyncRun.queued_at.desc()).limit(limit).offset(offset)
    )
    return list(rows), total


async def latest_channel_runs(
    db: AsyncSession, *, owner_id: str, channel_ids: list[str]
) -> tuple[dict[str, SyncRun], dict[str, datetime]]:
    if not channel_ids:
        return {}, {}

    ranked = (
        select(
            SyncRun.id.label("id"),
            func.row_number()
            .over(
                partition_by=SyncRun.channel_id,
                order_by=SyncRun.queued_at.desc(),
            )
            .label("position"),
        )
        .where(
            SyncRun.owner_id == owner_id,
            SyncRun.channel_id.in_(channel_ids),
        )
        .subquery()
    )
    latest = await db.scalars(
        select(SyncRun).join(ranked, ranked.c.id == SyncRun.id).where(ranked.c.position == 1)
    )
    latest_by_channel = {
        run.channel_id: run for run in latest if run.channel_id is not None
    }

    successes = await db.execute(
        select(SyncRun.channel_id, func.max(SyncRun.finished_at))
        .where(
            SyncRun.owner_id == owner_id,
            SyncRun.channel_id.in_(channel_ids),
            SyncRun.status.in_(("succeeded", "partial")),
        )
        .group_by(SyncRun.channel_id)
    )
    successful_at = {
        channel_id: finished_at
        for channel_id, finished_at in successes
        if channel_id is not None and finished_at is not None
    }
    return latest_by_channel, successful_at


async def quota_totals(
    db: AsyncSession, usage_date: date
) -> tuple[int, int]:
    row = (
        await db.execute(
            select(
                func.coalesce(func.sum(YouTubeAPIUsage.estimated_units), 0),
                func.coalesce(func.sum(YouTubeAPIUsage.call_count), 0),
            ).where(YouTubeAPIUsage.usage_date == usage_date)
        )
    ).one()
    return int(row[0]), int(row[1])


async def claim_sync_run(db: AsyncSession, sync_run_id: uuid.UUID) -> SyncRun | None:
    run = await db.scalar(
        select(SyncRun).where(SyncRun.id == sync_run_id).with_for_update()
    )
    if run is None or run.status != "queued":
        return None
    now = datetime.now(timezone.utc)
    run.status = "running"
    run.attempt_count += 1
    run.started_at = run.started_at or now
    run.next_retry_at = None
    run.updated_at = now
    await db.commit()
    await db.refresh(run)
    return run
