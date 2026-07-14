from fastapi import APIRouter, Depends, status

from app.auth.manager import get_user_manager
from app.auth.schemas import UserRead
from app.core.demo_policy import DemoOperation, require_demo_safe
from app.core.errors import ApplicationError
from app.dependencies import CurrentUserDep, DBSessionDep
from app.schemas.account import AccountDeleteRequest
from app.services import account_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_current_user(user: CurrentUserDep):
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    payload: AccountDeleteRequest,
    db_session: DBSessionDep,
    user: CurrentUserDep,
    user_manager=Depends(get_user_manager),
):
    require_demo_safe(DemoOperation.ACCOUNT_DELETE)
    if not await account_service.verify_password(user_manager, user, payload.current_password):
        raise ApplicationError(
            "CURRENT_PASSWORD_INVALID",
            "The current password is incorrect.",
            400,
        )
    await account_service.delete_account_data(db_session, user=user)
