from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshSession, User
from app.db.models.association_tables import (
    channel_categories,
    channel_tags,
    playlist_videos,
    subscription_import_tags,
    video_tags,
)
from app.db.models.category import Category
from app.db.models.channel import Channel
from app.db.models.folder import Folder
from app.db.models.playlist import Playlist
from app.db.models.subscription_import import SubscriptionImport, SubscriptionImportCandidate
from app.db.models.sync_run import SyncRun
from app.db.models.tag import Tag
from app.db.models.user_state import UserChannel, UserVideoState


async def delete_account_data(db_session: AsyncSession, *, user: User) -> None:
    """Delete personal data, then garbage-collect catalog channels with no followers."""
    uid = user.id
    channel_ids = list(
        (await db_session.scalars(select(UserChannel.channel_id).where(UserChannel.user_id == uid))).all()
    )
    if channel_ids:
        # Use a stable lock order so account deletion cannot race last-unfollow GC.
        await db_session.execute(
            select(Channel)
            .where(Channel.id.in_(sorted(channel_ids)))
            .order_by(Channel.id)
            .with_for_update()
        )

    # Explicit child deletion keeps SQLite tests correct even when FK enforcement is disabled.
    for table in (channel_categories, channel_tags, video_tags, playlist_videos, subscription_import_tags):
        await db_session.execute(delete(table).where(table.c.user_id == uid))
    await db_session.execute(delete(UserVideoState).where(UserVideoState.user_id == uid))
    await db_session.execute(delete(SyncRun).where(SyncRun.user_id == uid))
    import_ids = select(SubscriptionImport.id).where(SubscriptionImport.user_id == uid)
    await db_session.execute(delete(SubscriptionImportCandidate).where(SubscriptionImportCandidate.import_id.in_(import_ids)))
    await db_session.execute(delete(SubscriptionImport).where(SubscriptionImport.user_id == uid))
    await db_session.execute(delete(Playlist).where(Playlist.user_id == uid))
    await db_session.execute(delete(Category).where(Category.user_id == uid))
    await db_session.execute(delete(Tag).where(Tag.user_id == uid))
    await db_session.execute(delete(UserChannel).where(UserChannel.user_id == uid))
    await db_session.execute(delete(Folder).where(Folder.user_id == uid))
    await db_session.execute(delete(RefreshSession).where(RefreshSession.user_id == uid))
    await db_session.delete(user)

    for channel_id in channel_ids:
        remaining = await db_session.scalar(
            select(UserChannel.channel_id).where(UserChannel.channel_id == channel_id).limit(1)
        )
        if remaining is None:
            channel = await db_session.get(Channel, channel_id)
            if channel is not None:
                await db_session.delete(channel)
    await db_session.commit()


async def verify_password(user_manager, user: User, password: str) -> bool:
    verified, updated_hash = user_manager.password_helper.verify_and_update(
        password, user.hashed_password
    )
    if verified and updated_hash:
        user.hashed_password = updated_hash
    return verified
