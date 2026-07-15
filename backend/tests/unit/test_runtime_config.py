import pytest
from pydantic import ValidationError

from app.core.config import PLACEHOLDER_AUTH_SECRET, Settings


def full_settings(**overrides) -> Settings:
    values = {
        "APP_ENV": "test",
        "APP_MODE": "full",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/0",
        "API_ORIGIN": "http://localhost:5173",
        "YOUTUBE_API_KEY": "test-key",
    }
    values.update(overrides)
    return Settings(**values)


@pytest.mark.unit
def test_full_mode_defaults() -> None:
    configured = full_settings()

    assert configured.REGISTRATION_ENABLED is True
    assert configured.BACKGROUND_JOBS_ENABLED is True
    assert configured.DEMO_LOGIN_ENABLED is False
    assert configured.YOUTUBE_DAILY_QUOTA_BUDGET == 8_000


@pytest.mark.unit
def test_full_mode_accepts_blank_optional_demo_email() -> None:
    configured = full_settings(DEMO_USER_EMAIL="")

    assert configured.DEMO_USER_EMAIL is None


@pytest.mark.unit
def test_demo_mode_needs_no_redis_or_youtube_key() -> None:
    configured = full_settings(
        APP_MODE="demo",
        REDIS_URL=None,
        YOUTUBE_API_KEY=None,
        DEMO_USER_EMAIL="demo@example.com",
        DEMO_MAINTENANCE_SECRET="d" * 32,
    )

    assert configured.REGISTRATION_ENABLED is False
    assert configured.BACKGROUND_JOBS_ENABLED is False
    assert configured.DEMO_LOGIN_ENABLED is True
    assert configured.YOUTUBE_DAILY_QUOTA_BUDGET == 100


@pytest.mark.unit
@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"REDIS_URL": None}, "REDIS_URL"),
        ({"YOUTUBE_API_KEY": None}, "YOUTUBE_API_KEY"),
        ({"API_CORS_ORIGINS": "*"}, "Invalid CORS origin"),
        (
            {
                "YOUTUBE_OAUTH_ENABLED": True,
                "GOOGLE_CLIENT_ID": None,
                "GOOGLE_CLIENT_SECRET": None,
                "GOOGLE_REDIRECT_URI": None,
            },
            "Google OAuth settings",
        ),
    ],
)
def test_invalid_runtime_combinations(overrides, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        full_settings(**overrides)


@pytest.mark.unit
def test_production_rejects_placeholder_secret() -> None:
    with pytest.raises(ValidationError, match="AUTH_SECRET"):
        full_settings(APP_ENV="production", AUTH_SECRET=PLACEHOLDER_AUTH_SECRET)


@pytest.mark.unit
def test_production_accepts_secure_configuration() -> None:
    configured = full_settings(APP_ENV="production", AUTH_SECRET="s" * 32)
    assert configured.APP_ENV == "production"


@pytest.mark.unit
def test_insecure_oauth_transport_is_local_only() -> None:
    with pytest.raises(ValidationError, match="local development"):
        full_settings(APP_ENV="production", AUTH_SECRET="s" * 32, ALLOW_INSECURE_OAUTH_TRANSPORT=True)


@pytest.mark.unit
def test_explicit_runtime_options_and_oauth_defaults() -> None:
    configured = full_settings(
        REGISTRATION_ENABLED=False,
        BACKGROUND_JOBS_ENABLED=False,
        DEMO_LOGIN_ENABLED=True,
        YOUTUBE_DAILY_QUOTA_BUDGET=500,
        GOOGLE_CLIENT_ID="client",
        GOOGLE_CLIENT_SECRET="secret",
        GOOGLE_REDIRECT_URI="http://localhost:8000/oauth/callback",
    )

    assert configured.REGISTRATION_ENABLED is False
    assert configured.BACKGROUND_JOBS_ENABLED is False
    assert configured.DEMO_LOGIN_ENABLED is True
    assert configured.YOUTUBE_DAILY_QUOTA_BUDGET == 500
    assert configured.YOUTUBE_OAUTH_ENABLED is True


@pytest.mark.unit
@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"YOUTUBE_DAILY_QUOTA_BUDGET": 0}, "must be positive"),
        (
            {
                "APP_MODE": "demo",
                "REDIS_URL": None,
                "YOUTUBE_API_KEY": None,
                "DEMO_USER_EMAIL": None,
                "DEMO_MAINTENANCE_SECRET": "d" * 32,
            },
            "required in demo mode",
        ),
        (
            {
                "APP_MODE": "demo",
                "REDIS_URL": None,
                "YOUTUBE_API_KEY": None,
                "DEMO_USER_EMAIL": "demo@example.com",
                "DEMO_MAINTENANCE_SECRET": "short",
            },
            "at least 32 characters",
        ),
        ({"API_CORS_ORIGINS": "https://example.com/path"}, "must not contain a path"),
    ],
)
def test_additional_invalid_runtime_combinations(overrides, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        full_settings(**overrides)


@pytest.mark.unit
def test_get_redis_settings_rejects_disabled_redis() -> None:
    configured = full_settings(BACKGROUND_JOBS_ENABLED=False, REDIS_URL=None)

    with pytest.raises(RuntimeError, match="Redis is disabled"):
        configured.get_redis_settings()
