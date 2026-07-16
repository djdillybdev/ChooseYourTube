from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshSession, User
from app.db.models.channel import Channel
from app.db.models.category import Category
from app.db.models.folder import Folder
from app.db.models.playlist import Playlist
from app.db.models.subscription_import import SubscriptionImport
from app.db.models.sync_run import SyncRun
from app.db.models.tag import Tag


async def delete_account_data(
    db_session: AsyncSession,
    *,
    user: User,
) -> None:
    """Delete one user's account and owned graph in a single transaction."""
    owner_id = str(user.id)

    # Nullable sync references leave maintenance rows outside normal cascades.
    await db_session.execute(delete(SyncRun).where(SyncRun.owner_id == owner_id))
    await db_session.execute(
        delete(SubscriptionImport).where(SubscriptionImport.owner_id == owner_id)
    )
    # Playlists can reference channels, so they must be removed first.
    await db_session.execute(delete(Playlist).where(Playlist.owner_id == owner_id))
    await db_session.execute(delete(Tag).where(Tag.owner_id == owner_id))
    await db_session.execute(delete(Category).where(Category.owner_id == owner_id))
    # Channel deletion cascades videos and their association rows.
    await db_session.execute(delete(Channel).where(Channel.owner_id == owner_id))
    # Break self-references for SQLite as well as PostgreSQL before bulk deletion.
    await db_session.execute(
        update(Folder).where(Folder.owner_id == owner_id).values(parent_id=None)
    )
    await db_session.execute(delete(Folder).where(Folder.owner_id == owner_id))
    await db_session.execute(
        delete(RefreshSession).where(RefreshSession.user_id == user.id)
    )
    await db_session.delete(user)
    await db_session.commit()


async def verify_password(user_manager, user: User, password: str) -> bool:
    verified, updated_hash = user_manager.password_helper.verify_and_update(
        password, user.hashed_password
    )
    if verified and updated_hash:
        user.hashed_password = updated_hash
    return verified
