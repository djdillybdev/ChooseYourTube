from __future__ import annotations

import uuid
from urllib.parse import urlencode

from fastapi import APIRouter, File, Query, UploadFile, status
from fastapi.responses import RedirectResponse

from app.clients import youtube_oauth
from app.core.config import settings
from app.core.errors import ApplicationError
from app.dependencies import ArqDep, CurrentUserDep, DBSessionDep
from app.schemas.subscription_import import (
    CandidateSelectionUpdate,
    OAuthStartOut,
    SubscriptionCandidateState,
    SubscriptionImportCommit,
    SubscriptionImportDetailOut,
    SubscriptionImportOut,
)
from app.schemas.sync_run import SyncRunKind, SyncRunOut
from app.services import subscription_import_service, sync_service

router = APIRouter(tags=["Subscription imports"])


def _ensure_imports_enabled(*, oauth: bool = False) -> None:
    if settings.APP_MODE == "demo" or not settings.BACKGROUND_JOBS_ENABLED:
        raise ApplicationError(
            "FEATURE_DISABLED_IN_DEMO",
            "Subscription imports are disabled in the shared recruiter demo.",
            403,
        )
    if oauth and not settings.YOUTUBE_OAUTH_ENABLED:
        raise ApplicationError(
            "YOUTUBE_OAUTH_DISABLED",
            "Google subscription import is not configured for this installation.",
            403,
        )


def _frontend_redirect(path: str, **query: str) -> str:
    base = settings.API_ORIGIN.rstrip("/")
    suffix = f"?{urlencode(query)}" if query else ""
    return f"{base}{path}{suffix}"


@router.post(
    "/imports/subscriptions/csv",
    response_model=SubscriptionImportDetailOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_takeout_csv(
    db_session: DBSessionDep,
    user: CurrentUserDep,
    file: UploadFile = File(...),
):
    _ensure_imports_enabled()
    payload = await file.read(subscription_import_service.MAX_CSV_BYTES + 1)
    record = await subscription_import_service.collect_csv(
        db_session, owner_id=str(user.id), payload=payload
    )
    return await subscription_import_service.get_detail(
        db_session,
        import_id=record.id,
        owner_id=str(user.id),
        state=None,
        search=None,
        limit=50,
        offset=0,
    )


@router.get("/imports/youtube/oauth/start", response_model=OAuthStartOut)
async def start_youtube_oauth(db_session: DBSessionDep, user: CurrentUserDep):
    _ensure_imports_enabled(oauth=True)
    record, state_value = await subscription_import_service.create_oauth_import(
        db_session, owner_id=str(user.id)
    )
    return OAuthStartOut(
        import_id=record.id,
        authorization_url=youtube_oauth.authorization_url(state_value),
    )


@router.get("/imports/youtube/oauth/callback", include_in_schema=True)
async def youtube_oauth_callback(
    db_session: DBSessionDep,
    state: str | None = Query(None),
    code: str | None = Query(None),
    error: str | None = Query(None),
):
    if not state:
        return RedirectResponse(
            _frontend_redirect(
                "/settings/imports", oauth_error="OAUTH_STATE_INVALID"
            ),
            status_code=303,
        )
    try:
        record = await subscription_import_service.consume_oauth_state(db_session, state)
    except ApplicationError as exc:
        return RedirectResponse(
            _frontend_redirect("/settings/imports", oauth_error=exc.code),
            status_code=303,
        )
    if error or not code:
        await subscription_import_service.fail_collection(
            db_session,
            record,
            "OAUTH_CONSENT_DENIED",
            "Google authorization was cancelled or denied.",
        )
    else:
        try:
            subscriptions = await youtube_oauth.collect_subscriptions(code, state)
            await subscription_import_service.store_oauth_candidates(
                db_session, import_record=record, subscriptions=subscriptions
            )
        except ApplicationError as exc:
            await subscription_import_service.fail_collection(
                db_session, record, exc.code, exc.message
            )
    return RedirectResponse(
        _frontend_redirect(f"/settings/imports/{record.id}"), status_code=303
    )


@router.get("/imports/{import_id}", response_model=SubscriptionImportDetailOut)
async def get_import(
    import_id: uuid.UUID,
    db_session: DBSessionDep,
    user: CurrentUserDep,
    state: SubscriptionCandidateState | None = Query(None),
    search: str | None = Query(None, max_length=255),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await subscription_import_service.get_detail(
        db_session,
        import_id=import_id,
        owner_id=str(user.id),
        state=state,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.patch("/imports/{import_id}/candidates", response_model=SubscriptionImportOut)
async def update_candidates(
    import_id: uuid.UUID,
    payload: CandidateSelectionUpdate,
    db_session: DBSessionDep,
    user: CurrentUserDep,
):
    _ensure_imports_enabled()
    return await subscription_import_service.update_selection(
        db_session,
        import_id=import_id,
        owner_id=str(user.id),
        payload=payload,
    )


@router.post(
    "/imports/{import_id}/commit",
    response_model=SyncRunOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def commit_import(
    import_id: uuid.UUID,
    payload: SubscriptionImportCommit,
    db_session: DBSessionDep,
    redis: ArqDep,
    user: CurrentUserDep,
):
    _ensure_imports_enabled()
    record = await subscription_import_service.prepare_commit(
        db_session,
        import_id=import_id,
        owner_id=str(user.id),
        payload=payload,
    )
    try:
        run = await sync_service.enqueue_run(
            db_session,
            redis,
            owner_id=str(user.id),
            kind=SyncRunKind.SUBSCRIPTION_IMPORT,
            subscription_import_id=record.id,
        )
    except ApplicationError as exc:
        await subscription_import_service.fail_execution(
            db_session,
            import_id=record.id,
            owner_id=str(user.id),
            code=exc.code,
            message=exc.message,
        )
        raise
    return sync_service.to_sync_run_out(run)
