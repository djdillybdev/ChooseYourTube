from fastapi import APIRouter, Depends, Request
from fastapi_users import exceptions as user_exceptions

from app.auth.manager import get_user_manager
from app.core.config import settings
from app.core.errors import ApplicationError
from app.db.session import get_db_session
from app.routers.auth_session import issue_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/demo")
async def demo_login(
    request: Request,
    db_session=Depends(get_db_session),
    user_manager=Depends(get_user_manager),
):
    try:
        user = await user_manager.get_by_email(str(settings.DEMO_USER_EMAIL))
    except user_exceptions.UserNotExists as exc:
        raise ApplicationError(
            "DEMO_ACCOUNT_UNAVAILABLE",
            "The demo account is temporarily unavailable.",
            503,
            retryable=True,
        ) from exc
    if not user.is_active:
        raise ApplicationError(
            "DEMO_ACCOUNT_UNAVAILABLE",
            "The demo account is temporarily unavailable.",
            503,
            retryable=True,
        )
    return await issue_session(db_session, user, request)
