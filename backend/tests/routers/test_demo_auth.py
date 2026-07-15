from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from fastapi_users import exceptions as user_exceptions

from app.core.errors import ApplicationError
from app.routers.demo_auth import demo_login


def request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/auth/demo",
            "headers": [],
            "client": ("127.0.0.1", 1234),
        }
    )


@pytest.mark.asyncio
async def test_demo_login_issues_normal_session(monkeypatch):
    user = MagicMock(is_active=True)
    manager = AsyncMock()
    manager.get_by_email.return_value = user
    monkeypatch.setattr("app.routers.demo_auth.settings.DEMO_USER_EMAIL", "demo@example.com")
    with patch(
        "app.routers.demo_auth.issue_session",
        new=AsyncMock(return_value={"access_token": "access", "refresh_token": "refresh"}),
    ) as issue:
        result = await demo_login(request(), MagicMock(), manager)
    assert result["access_token"] == "access"
    manager.get_by_email.assert_awaited_once_with("demo@example.com")
    issue.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("missing", [True, False])
async def test_demo_login_hides_missing_and_inactive_accounts(missing):
    manager = AsyncMock()
    if missing:
        manager.get_by_email.side_effect = user_exceptions.UserNotExists()
    else:
        manager.get_by_email.return_value = MagicMock(is_active=False)

    with pytest.raises(ApplicationError) as error:
        await demo_login(request(), MagicMock(), manager)
    assert error.value.code == "DEMO_ACCOUNT_UNAVAILABLE"
    assert error.value.retryable is True
