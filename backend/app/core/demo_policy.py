from enum import StrEnum

from app.core.config import settings
from app.core.errors import ApplicationError


class DemoOperation(StrEnum):
    CHANNEL_CREATE = "channel_create"
    CHANNEL_DELETE = "channel_delete"
    VIDEO_DELETE = "video_delete"
    ACCOUNT_DELETE = "account_delete"


def require_demo_safe(operation: DemoOperation) -> None:
    """Reject operations that must never mutate destructive demo state."""
    if settings.APP_MODE != "demo":
        return
    raise ApplicationError(
        "FEATURE_DISABLED_IN_DEMO",
        "This operation is disabled in the shared demo.",
        403,
    )
