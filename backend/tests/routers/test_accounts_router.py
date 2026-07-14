from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core import demo_policy
from app.core.errors import ApplicationError
from app.routers import accounts
from app.schemas.account import AccountDeleteRequest


@pytest.mark.asyncio
async def test_delete_account_rejects_incorrect_password(monkeypatch):
    monkeypatch.setattr(demo_policy.settings, "APP_MODE", "full")
    monkeypatch.setattr(accounts.account_service, "verify_password", AsyncMock(return_value=False))
    delete_mock = AsyncMock()
    monkeypatch.setattr(accounts.account_service, "delete_account_data", delete_mock)

    with pytest.raises(ApplicationError) as raised:
        await accounts.delete_current_user(
            AccountDeleteRequest(current_password="wrong"),
            AsyncMock(),
            MagicMock(),
            MagicMock(),
        )

    assert raised.value.code == "CURRENT_PASSWORD_INVALID"
    delete_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_account_deletes_after_password_verification(monkeypatch):
    monkeypatch.setattr(demo_policy.settings, "APP_MODE", "full")
    monkeypatch.setattr(accounts.account_service, "verify_password", AsyncMock(return_value=True))
    delete_mock = AsyncMock()
    monkeypatch.setattr(accounts.account_service, "delete_account_data", delete_mock)
    session = AsyncMock()
    user = MagicMock()

    await accounts.delete_current_user(
        AccountDeleteRequest(current_password="correct"), session, user, MagicMock()
    )

    delete_mock.assert_awaited_once_with(session, user=user)
