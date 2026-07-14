import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import exceptions as fu_exceptions
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.backend import get_jwt_strategy
from app.auth.manager import get_user_manager
from app.auth.models import RefreshSession
from app.core.config import settings
from app.core.errors import ApplicationError
from app.db.session import get_db_session

router = APIRouter(prefix="/auth/session", tags=["auth"])


class SessionLoginRequest(BaseModel):
    email: EmailStr
    password: str


class SessionRefreshRequest(BaseModel):
    refresh_token: str


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _create_refresh_token() -> str:
    return secrets.token_urlsafe(settings.REFRESH_TOKEN_BYTES)


async def _mint_access_token(user) -> str:
    strategy = get_jwt_strategy()
    return await strategy.write_token(user)


async def issue_session(
    db_session: AsyncSession, user, request: Request
) -> dict[str, str | int]:
    _, refresh_token = await _create_refresh_session(
        db_session,
        user.id,
        request.headers.get("user-agent"),
        request.client.host if request.client else None,
    )
    access_token = await _mint_access_token(user)
    await db_session.commit()
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "access_expires_in": settings.ACCESS_TOKEN_TTL_SECONDS,
        "refresh_token": refresh_token,
        "refresh_expires_in": settings.REFRESH_TOKEN_TTL_SECONDS,
    }


async def _create_refresh_session(
    db_session: AsyncSession,
    user_id: uuid.UUID,
    user_agent: str | None,
    ip_address: str | None,
    *,
    session_id: uuid.UUID | None = None,
    parent_id: uuid.UUID | None = None,
) -> tuple[RefreshSession, str]:
    token = _create_refresh_token()
    now = _utcnow()
    row = RefreshSession(
        user_id=user_id,
        session_id=session_id or uuid.uuid4(),
        token_hash=_hash_token(token),
        parent_id=parent_id,
        user_agent=user_agent,
        ip_address=ip_address,
        created_at=now,
        expires_at=now + timedelta(seconds=settings.REFRESH_TOKEN_TTL_SECONDS),
    )
    db_session.add(row)
    await db_session.flush()
    return row, token


async def _revoke_session_chain(db_session: AsyncSession, session_id: uuid.UUID) -> None:
    now = _utcnow()
    await db_session.execute(
        update(RefreshSession)
        .where(RefreshSession.session_id == session_id, RefreshSession.revoked_at.is_(None))
        .values(revoked_at=now, last_used_at=now)
    )


@router.post("/login")
async def session_login(
    payload: SessionLoginRequest,
    request: Request,
    db_session: AsyncSession = Depends(get_db_session),
    user_manager=Depends(get_user_manager),
):
    if settings.APP_MODE == "demo":
        raise ApplicationError(
            "FEATURE_DISABLED_IN_DEMO",
            "Password login is disabled in the shared recruiter demo.",
            403,
        )
    credentials = OAuth2PasswordRequestForm(
        username=payload.email,
        password=payload.password,
    )
    user = await user_manager.authenticate(credentials)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS"},
        )

    return await issue_session(db_session, user, request)


@router.post("/refresh")
async def session_refresh(
    payload: SessionRefreshRequest,
    request: Request,
    db_session: AsyncSession = Depends(get_db_session),
    user_manager=Depends(get_user_manager),
):
    if not payload.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "REFRESH_MISSING"},
        )

    token_hash = _hash_token(payload.refresh_token)
    refresh_session = await db_session.scalar(
        select(RefreshSession).where(RefreshSession.token_hash == token_hash)
    )

    if refresh_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "REFRESH_INVALID"},
        )

    now = _utcnow()
    if refresh_session.revoked_at is not None or refresh_session.replaced_by_id is not None:
        await _revoke_session_chain(db_session, refresh_session.session_id)
        await db_session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "SESSION_REVOKED"},
        )

    if refresh_session.expires_at <= now:
        refresh_session.revoked_at = now
        refresh_session.last_used_at = now
        await db_session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "REFRESH_EXPIRED"},
        )

    try:
        user = await user_manager.get(refresh_session.user_id)
    except fu_exceptions.UserNotExists as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "REFRESH_INVALID"},
        ) from exc
    new_row, new_refresh_token = await _create_refresh_session(
        db_session,
        user.id,
        request.headers.get("user-agent"),
        request.client.host if request.client else None,
        session_id=refresh_session.session_id,
        parent_id=refresh_session.id,
    )
    refresh_session.replaced_by_id = new_row.id
    refresh_session.revoked_at = now
    refresh_session.last_used_at = now

    access_token = await _mint_access_token(user)
    await db_session.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "access_expires_in": settings.ACCESS_TOKEN_TTL_SECONDS,
        "refresh_token": new_refresh_token,
        "refresh_expires_in": settings.REFRESH_TOKEN_TTL_SECONDS,
    }


@router.post("/logout")
async def session_logout(
    payload: SessionRefreshRequest,
    db_session: AsyncSession = Depends(get_db_session),
):
    if payload.refresh_token:
        token_hash = _hash_token(payload.refresh_token)
        refresh_session = await db_session.scalar(
            select(RefreshSession).where(RefreshSession.token_hash == token_hash)
        )
        if refresh_session is not None:
            await _revoke_session_chain(db_session, refresh_session.session_id)
            await db_session.commit()
            return {"ok": True}

    return {"ok": True}
