from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import ApplicationError
from app.db.models.sync_run import YouTubeAPIUsage
from app.db.session import sessionmanager


async def _lock_day(db: AsyncSession, usage_date: date) -> None:
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        # A project-wide transaction lock makes budget reservations atomic across workers.
        await db.execute(
            text("SELECT pg_advisory_xact_lock(:key)"),
            {"key": 2_000_000_000 + usage_date.toordinal()},
        )


async def _bucket(
    db: AsyncSession, usage_date: date, operation: str, outcome: str
) -> YouTubeAPIUsage:
    row = await db.scalar(
        select(YouTubeAPIUsage).where(
            YouTubeAPIUsage.usage_date == usage_date,
            YouTubeAPIUsage.operation == operation,
            YouTubeAPIUsage.outcome == outcome,
        )
    )
    if row is None:
        row = YouTubeAPIUsage(
            usage_date=usage_date,
            operation=operation,
            outcome=outcome,
            estimated_units=0,
            call_count=0,
        )
        db.add(row)
        await db.flush()
    return row


async def reserve_quota(operation: str, units: int = 1) -> date:
    usage_date = datetime.now(timezone.utc).date()
    async with sessionmanager.session() as db:
        await _lock_day(db, usage_date)
        used = int(
            await db.scalar(
                select(func.coalesce(func.sum(YouTubeAPIUsage.estimated_units), 0)).where(
                    YouTubeAPIUsage.usage_date == usage_date
                )
            )
            or 0
        )
        budget = int(settings.YOUTUBE_DAILY_QUOTA_BUDGET or 0)
        if used + units > budget:
            raise ApplicationError(
                "YOUTUBE_QUOTA_EXHAUSTED",
                "YouTube refresh is temporarily unavailable because the daily quota was reached.",
                429,
                retryable=False,
            )
        reserved = await _bucket(db, usage_date, operation, "reserved")
        reserved.estimated_units += units
        reserved.call_count += 1
        await db.commit()
    return usage_date


async def finalize_quota(
    usage_date: date, operation: str, outcome: str, units: int = 1
) -> None:
    async with sessionmanager.session() as db:
        await _lock_day(db, usage_date)
        reserved = await _bucket(db, usage_date, operation, "reserved")
        target = await _bucket(db, usage_date, operation, outcome)
        if reserved.call_count > 0:
            reserved.call_count -= 1
            reserved.estimated_units = max(0, reserved.estimated_units - units)
        target.call_count += 1
        target.estimated_units += units
        await db.commit()
