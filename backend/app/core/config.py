from __future__ import annotations

from typing import Literal
from urllib.parse import urlparse

from arq.connections import RedisSettings
from pydantic import EmailStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PLACEHOLDER_AUTH_SECRET = "change-me-in-production-with-at-least-32-characters"


class Settings(BaseSettings):
    """Validated application settings shared by the API and worker."""

    APP_ENV: Literal["local", "test", "production"] = "local"
    APP_MODE: Literal["full", "demo"] = "full"

    DATABASE_URL: str
    DATABASE_POOL_MODE: Literal["persistent", "serverless"] = "persistent"
    REDIS_URL: str | None = None
    API_ORIGIN: str = "http://localhost:5173"
    API_CORS_ORIGINS: str | None = None
    YOUTUBE_API_KEY: str | None = None
    AUTH_SECRET: str = PLACEHOLDER_AUTH_SECRET

    REGISTRATION_ENABLED: bool | None = None
    BACKGROUND_JOBS_ENABLED: bool | None = None
    YOUTUBE_OAUTH_ENABLED: bool | None = None
    DEMO_LOGIN_ENABLED: bool | None = None
    YOUTUBE_DAILY_QUOTA_BUDGET: int | None = None
    DEMO_USER_EMAIL: EmailStr | None = None
    DEMO_MAINTENANCE_SECRET: str | None = None
    CRON_SECRET: str | None = None

    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None
    ALLOW_INSECURE_OAUTH_TRANSPORT: bool = False

    ACCESS_TOKEN_TTL_SECONDS: int = 60 * 15
    REFRESH_TOKEN_TTL_SECONDS: int = 60 * 60 * 24 * 30
    REFRESH_TOKEN_BYTES: int = 48
    SHORTS_MAX_SECONDS: int = 60
    echo_sql: bool = False
    debug_logs: bool = False
    enable_startup_schema_check: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("DEMO_USER_EMAIL", mode="before")
    @classmethod
    def empty_demo_email_is_unset(cls, value: object) -> object:
        """Allow the shared full-mode env template to leave demo email blank."""
        return None if value == "" else value

    @model_validator(mode="after")
    def validate_runtime(self) -> "Settings":
        demo = self.APP_MODE == "demo"
        if self.REGISTRATION_ENABLED is None:
            self.REGISTRATION_ENABLED = not demo
        if self.BACKGROUND_JOBS_ENABLED is None:
            self.BACKGROUND_JOBS_ENABLED = not demo
        if self.DEMO_LOGIN_ENABLED is None:
            self.DEMO_LOGIN_ENABLED = demo
        if self.YOUTUBE_DAILY_QUOTA_BUDGET is None:
            self.YOUTUBE_DAILY_QUOTA_BUDGET = 100 if demo else 8_000
        if self.YOUTUBE_OAUTH_ENABLED is None:
            self.YOUTUBE_OAUTH_ENABLED = bool(
                not demo
                and self.GOOGLE_CLIENT_ID
                and self.GOOGLE_CLIENT_SECRET
                and self.GOOGLE_REDIRECT_URI
            )

        if self.YOUTUBE_DAILY_QUOTA_BUDGET < 1:
            raise ValueError("YOUTUBE_DAILY_QUOTA_BUDGET must be positive")
        if self.BACKGROUND_JOBS_ENABLED and not self.REDIS_URL:
            raise ValueError("REDIS_URL is required when background jobs are enabled")
        if not demo and not self.YOUTUBE_API_KEY:
            raise ValueError("YOUTUBE_API_KEY is required in full mode")
        if demo and (not self.DEMO_USER_EMAIL or not self.maintenance_secret):
            raise ValueError(
                "DEMO_USER_EMAIL and CRON_SECRET (or DEMO_MAINTENANCE_SECRET) "
                "are required in demo mode"
            )
        if demo and self.maintenance_secret and len(self.maintenance_secret) < 32:
            raise ValueError(
                "The demo maintenance secret must be at least 32 characters"
            )

        oauth_values = (
            self.GOOGLE_CLIENT_ID,
            self.GOOGLE_CLIENT_SECRET,
            self.GOOGLE_REDIRECT_URI,
        )
        if self.YOUTUBE_OAUTH_ENABLED and not all(oauth_values):
            raise ValueError("Google OAuth settings are required when OAuth is enabled")
        if self.ALLOW_INSECURE_OAUTH_TRANSPORT and self.APP_ENV != "local":
            raise ValueError(
                "Insecure OAuth transport is allowed only in local development"
            )

        for origin in self.cors_origins:
            parsed = urlparse(origin)
            if (
                origin == "*"
                or parsed.scheme not in {"http", "https"}
                or not parsed.netloc
            ):
                raise ValueError(f"Invalid CORS origin: {origin}")
            if (
                parsed.path not in {"", "/"}
                or parsed.params
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError(f"CORS origins must not contain a path: {origin}")

        if self.APP_ENV == "production":
            if (
                self.AUTH_SECRET == PLACEHOLDER_AUTH_SECRET
                or len(self.AUTH_SECRET) < 32
            ):
                raise ValueError(
                    "AUTH_SECRET must be a non-placeholder value of at least 32 characters"
                )
        return self

    def get_redis_settings(self) -> RedisSettings:
        if not self.REDIS_URL:
            raise RuntimeError("Redis is disabled for this runtime")
        return RedisSettings.from_dsn(self.REDIS_URL)

    @property
    def cors_origins(self) -> list[str]:
        value = self.API_CORS_ORIGINS or self.API_ORIGIN
        return [
            origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()
        ]

    @property
    def public_features(self) -> dict[str, bool]:
        return {
            "registration": bool(self.REGISTRATION_ENABLED),
            "background_jobs": bool(self.BACKGROUND_JOBS_ENABLED),
            "youtube_oauth": bool(self.YOUTUBE_OAUTH_ENABLED),
            "demo_login": bool(self.DEMO_LOGIN_ENABLED),
            "subscription_imports": bool(
                self.APP_MODE == "full" and self.BACKGROUND_JOBS_ENABLED
            ),
        }

    @property
    def maintenance_secret(self) -> str | None:
        """Return Vercel's canonical cron secret with the legacy setting as fallback."""
        return self.CRON_SECRET or self.DEMO_MAINTENANCE_SECRET


settings = Settings()  # type: ignore[call-arg]
