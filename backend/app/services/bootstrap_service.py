from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import UserRead
from app.core.version import APP_VERSION
from app.core.config import settings
from app.schemas.bootstrap import AppBootstrapOut, RuntimeFeaturesOut, RuntimeMetadataOut
from app.schemas.channel import ChannelOut
from app.schemas.tag import TagOut
from app.services import channel_service, folder_service, playlist_service, tag_service


async def _all_channels(db_session: AsyncSession, owner_id: str) -> list[ChannelOut]:
    items: list[ChannelOut] = []
    offset = 0
    while True:
        page = await channel_service.get_all_channels(
            db_session=db_session,
            owner_id=owner_id,
            limit=200,
            offset=offset,
        )
        items.extend(page.items)
        if not page.has_more:
            return items
        offset += page.limit


async def _all_tags(db_session: AsyncSession, owner_id: str) -> list[TagOut]:
    items: list[TagOut] = []
    offset = 0
    while True:
        page = await tag_service.get_all_tags(
            db_session=db_session,
            owner_id=owner_id,
            limit=200,
            offset=offset,
        )
        items.extend(page.items)
        if not page.has_more:
            return items
        offset += page.limit


async def get_app_bootstrap(
    db_session: AsyncSession,
    user: User,
) -> AppBootstrapOut:
    owner_id = str(user.id)
    folders = await folder_service.get_tree(db_session, owner_id=owner_id)
    channels = await _all_channels(db_session, owner_id)
    tags = await _all_tags(db_session, owner_id)
    watch_later = await playlist_service.get_watch_later_detail(
        db_session, owner_id=owner_id
    )

    return AppBootstrapOut(
        current_user=UserRead.model_validate(user),
        folders=folders,
        channels=channels,
        tags=tags,
        watch_later=watch_later,
        runtime=RuntimeMetadataOut(
            name="ChooseYourTube",
            version=APP_VERSION,
            mode=settings.APP_MODE,
            features=RuntimeFeaturesOut(**settings.public_features),
        ),
    )
