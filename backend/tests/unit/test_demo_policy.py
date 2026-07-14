import pytest

from app.core import demo_policy
from app.core.demo_policy import DemoOperation, require_demo_safe
from app.core.errors import ApplicationError


def test_destructive_operation_is_allowed_in_full_mode(monkeypatch):
    monkeypatch.setattr(demo_policy.settings, "APP_MODE", "full")
    require_demo_safe(DemoOperation.CHANNEL_DELETE)


def test_destructive_operation_is_rejected_in_demo_mode(monkeypatch):
    monkeypatch.setattr(demo_policy.settings, "APP_MODE", "demo")
    with pytest.raises(ApplicationError) as raised:
        require_demo_safe(DemoOperation.ACCOUNT_DELETE)
    assert raised.value.code == "FEATURE_DISABLED_IN_DEMO"
    assert raised.value.status_code == 403
