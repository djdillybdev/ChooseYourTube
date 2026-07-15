from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.config import settings
from app.core.errors import ApplicationError
from app.db.crud import crud_sync_run
from app.db.models.sync_run import SyncRun
from app.db.session import get_db_session
from app.schemas.sync_run import SyncRunKind, SyncRunOut, SyncRunStatus
from app.services import demo_service
from app.services.sync_service import SyncProgress, to_sync_run_out

router = APIRouter(prefix="/internal/demo", tags=["internal"], include_in_schema=False)
logger = logging.getLogger(__name__)


def _authorize(authorization: str | None) -> None:
    expected = settings.maintenance_secret
    supplied = authorization.removeprefix("Bearer ") if authorization else ""
    if not expected or not secrets.compare_digest(supplied, expected):
        raise ApplicationError("CRON_UNAUTHORIZED", "Cron authorization failed.", 401)


async def _demo_owner(db: AsyncSession) -> str:
    user = await db.scalar(
        select(User).where(User.__table__.c.email == str(settings.DEMO_USER_EMAIL))
    )
    if user is None or not user.is_active:
        raise ApplicationError(
            "DEMO_ACCOUNT_UNAVAILABLE",
            "The demo account has not been seeded.",
            503,
            retryable=True,
        )
    return str(user.id)


@router.get("/maintenance", response_model=SyncRunOut)
async def maintain_demo(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db_session),
) -> SyncRunOut:
    _authorize(authorization)
    owner_id = await _demo_owner(db)
    run_id = demo_service.maintenance_run_id()
    run = await crud_sync_run.get_sync_run(db, run_id, owner_id=owner_id)
    now = datetime.now(timezone.utc)
    if run is not None:
        if run.status in {"succeeded", "partial", "failed"}:
            return to_sync_run_out(run)
        started_at = run.started_at or run.queued_at
        if started_at > now - timedelta(minutes=10):
            return to_sync_run_out(run)
        run.status = SyncRunStatus.RUNNING.value
        run.attempt_count += 1
        run.started_at = now
    else:
        run = SyncRun(
            id=run_id,
            owner_id=owner_id,
            kind=SyncRunKind.DEMO_MAINTENANCE.value,
            status=SyncRunStatus.RUNNING.value,
            attempt_count=1,
            max_attempts=1,
            queued_at=now,
            started_at=now,
        )
        db.add(run)
    await db.commit()

    progress = SyncProgress()
    refresh_error: ApplicationError | None = None
    try:
        try:
            progress = await demo_service.refresh_curated_channels_from_rss(owner_id)
        except TimeoutError:
            refresh_error = ApplicationError(
                "DEMO_REFRESH_TIMEOUT", "The bounded daily refresh timed out.", 503
            )
        except ApplicationError as exc:
            refresh_error = exc

        await demo_service.reset_demo_state(db, owner_id=owner_id)
        await demo_service.cleanup_expired_sessions(db)

        persisted = await crud_sync_run.get_sync_run(db, run_id, owner_id=owner_id)
        if persisted is None:
            raise RuntimeError("Demo maintenance run disappeared")
        demo_service.apply_progress(persisted, progress)
        if refresh_error is not None or progress.failed:
            code = refresh_error.code if refresh_error else "DEMO_REFRESH_PARTIAL"
            message = (
                refresh_error.message
                if refresh_error
                else "Some curated channels could not be refreshed."
            )
            demo_service.finish_run(
                persisted, SyncRunStatus.PARTIAL, code=code, message=message
            )
        else:
            demo_service.finish_run(persisted, SyncRunStatus.SUCCEEDED)
        await db.commit()
        await db.refresh(persisted)
        logger.info(
            "demo_maintenance_completed",
            extra={
                "sync_run_id": str(run_id),
                "owner_id": owner_id,
                "task_kind": SyncRunKind.DEMO_MAINTENANCE.value,
                "outcome": persisted.status,
            },
        )
        return to_sync_run_out(persisted)
    except Exception as exc:
        logger.exception(
            "demo_maintenance_failed",
            extra={
                "sync_run_id": str(run_id),
                "owner_id": owner_id,
                "outcome": "failed",
            },
        )
        await db.rollback()
        persisted = await crud_sync_run.get_sync_run(db, run_id, owner_id=owner_id)
        if persisted is not None:
            demo_service.finish_run(
                persisted,
                SyncRunStatus.FAILED,
                code="DEMO_RESET_FAILED",
                message="The demo state could not be restored.",
            )
            await db.commit()
        raise ApplicationError(
            "DEMO_MAINTENANCE_FAILED",
            "Demo maintenance failed; the last durable dataset remains available.",
            500,
        ) from exc
