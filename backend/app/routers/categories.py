from fastapi import APIRouter, status

from ..dependencies import CurrentUserDep, DBSessionDep
from ..schemas.category import (
    CategoryChannelsUpdate,
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    ChannelCategoriesOut,
    ChannelCategoriesUpdate,
)
from ..services import category_service

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=list[CategoryOut])
async def list_categories(db_session: DBSessionDep, user: CurrentUserDep):
    return await category_service.list_categories(db_session, owner_id=str(user.id))


@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate, db_session: DBSessionDep, user: CurrentUserDep
):
    return await category_service.create_category(
        payload, db_session, owner_id=str(user.id)
    )


@router.put("/channels/{channel_id}", response_model=ChannelCategoriesOut)
async def replace_channel_categories(
    channel_id: str,
    payload: ChannelCategoriesUpdate,
    db_session: DBSessionDep,
    user: CurrentUserDep,
):
    return await category_service.replace_channel_categories(
        channel_id, payload, db_session, owner_id=str(user.id)
    )


@router.get("/{category_id}", response_model=CategoryOut)
async def get_category(
    category_id: str, db_session: DBSessionDep, user: CurrentUserDep
):
    return await category_service.get_category_out(
        category_id, db_session, owner_id=str(user.id)
    )


@router.patch("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: str,
    payload: CategoryUpdate,
    db_session: DBSessionDep,
    user: CurrentUserDep,
):
    return await category_service.update_category(
        category_id, payload, db_session, owner_id=str(user.id)
    )


@router.put("/{category_id}/channels", response_model=CategoryOut)
async def replace_category_channels(
    category_id: str,
    payload: CategoryChannelsUpdate,
    db_session: DBSessionDep,
    user: CurrentUserDep,
):
    return await category_service.replace_category_channels(
        category_id, payload, db_session, owner_id=str(user.id)
    )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str, db_session: DBSessionDep, user: CurrentUserDep
):
    await category_service.delete_category(
        category_id, db_session, owner_id=str(user.id)
    )
