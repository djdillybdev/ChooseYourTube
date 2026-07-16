import uuid

import pytest

from app.auth.models import User
from app.services.bootstrap_service import get_app_bootstrap


@pytest.mark.asyncio
async def test_bootstrap_returns_owned_navigation_data_and_watch_later(db_session):
    user = User(
        id=uuid.uuid4(),
        email="bootstrap@example.com",
        hashed_password="not-used",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )

    result = await get_app_bootstrap(db_session, user)

    assert result.current_user.id == user.id
    assert result.folders == []
    assert result.channels == []
    assert result.tags == []
    assert result.watch_later.system_key == "watch_later"
    assert result.runtime.name == "ChooseYourTube"
