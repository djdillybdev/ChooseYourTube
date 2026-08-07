import uuid
import logging

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from app.auth.models import User
from app.core.config import settings
from app.db.session import get_db_session
from app.db.session import sessionmanager


logger = logging.getLogger(__name__)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.AUTH_SECRET
    verification_token_secret = settings.AUTH_SECRET

    async def on_after_register(self, user: User, request: Request | None = None):
        try:
            from app.services.playlist_service import ensure_watch_later

            async with sessionmanager.session() as session:
                await ensure_watch_later(session, owner_id=str(user.id))
        except Exception:
            # Registration has already committed. The lazy endpoint repairs this safely.
            logger.exception(
                "watch_later_initialization_failed", extra={"owner_id": str(user.id)}
            )


async def get_user_db(session=Depends(get_db_session)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
