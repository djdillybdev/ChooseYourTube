from fastapi import APIRouter

from app.dependencies import CurrentUserDep, DBSessionDep
from app.schemas.bootstrap import AppBootstrapOut
from app.services import bootstrap_service

router = APIRouter(prefix="/app", tags=["Application"])


@router.get("/bootstrap", response_model=AppBootstrapOut)
async def get_app_bootstrap(db_session: DBSessionDep, user: CurrentUserDep):
    return await bootstrap_service.get_app_bootstrap(db_session, user)
