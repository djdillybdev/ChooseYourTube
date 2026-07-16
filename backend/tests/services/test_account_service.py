import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from app.auth.models import RefreshSession, User
from app.db.models.folder import Folder
from app.db.models.category import Category
from app.db.models.playlist import Playlist
from app.db.models.sync_run import SyncRun
from app.db.models.tag import Tag
from app.services.account_service import delete_account_data


@pytest.mark.asyncio
async def test_delete_account_removes_owned_graph_and_preserves_other_user(db_session):
    user = User(id=uuid.uuid4(), email="delete@example.com", hashed_password="hash")
    other = User(id=uuid.uuid4(), email="keep@example.com", hashed_password="hash")
    db_session.add_all([user, other])
    await db_session.flush()
    owner_id = str(user.id)
    other_id = str(other.id)
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            Folder(id="delete-folder", owner_id=owner_id, name="Delete"),
            Category(
                id="delete-category",
                owner_id=owner_id,
                name="Delete",
                normalized_name="delete",
            ),
            Playlist(id="delete-playlist", owner_id=owner_id, name="Delete"),
            Tag(id="delete-tag", owner_id=owner_id, name="delete"),
            SyncRun(owner_id=owner_id, kind="demo_maintenance"),
            Folder(id="keep-folder", owner_id=other_id, name="Keep"),
            Category(
                id="keep-category",
                owner_id=other_id,
                name="Keep",
                normalized_name="keep",
            ),
            RefreshSession(
                user_id=user.id,
                session_id=uuid.uuid4(),
                token_hash="a" * 64,
                created_at=now,
                expires_at=now + timedelta(days=1),
            ),
        ]
    )
    await db_session.commit()

    await delete_account_data(db_session, user=user)

    assert await db_session.get(User, user.id) is None
    assert await db_session.get(User, other.id) is not None
    assert await db_session.scalar(
        select(func.count(Folder.id)).where(Folder.owner_id == owner_id)
    ) == 0
    assert await db_session.scalar(
        select(func.count(Playlist.id)).where(Playlist.owner_id == owner_id)
    ) == 0
    assert await db_session.scalar(
        select(func.count(SyncRun.id)).where(SyncRun.owner_id == owner_id)
    ) == 0
    assert await db_session.scalar(
        select(func.count(Folder.id)).where(Folder.owner_id == other_id)
    ) == 1
    assert await db_session.scalar(
        select(func.count(Category.id)).where(Category.owner_id == owner_id)
    ) == 0
    assert await db_session.scalar(
        select(func.count(Category.id)).where(Category.owner_id == other_id)
    ) == 1
