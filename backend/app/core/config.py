from pydantic_settings import BaseSettings, SettingsConfigDict
from arq.connections import RedisSettings


class Settings(BaseSettings):
    # DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/yt"
    DATABASE_URL: str
    # REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_URL: str
    # API_ORIGIN: str = "http://localhost:5173"
    API_ORIGIN: str
    API_CORS_ORIGINS: str | None = None
    YOUTUBE_API_KEY: str
    AUTH_SECRET: str = "change-me-in-production-with-at-least-32-characters"
    ACCESS_TOKEN_TTL_SECONDS: int = 60 * 15
    REFRESH_TOKEN_TTL_SECONDS: int = 60 * 60 * 24 * 30
    REFRESH_TOKEN_BYTES: int = 48
    SHORTS_MAX_SECONDS: int = 60
    echo_sql: bool = False
    debug_logs: bool = True
    enable_startup_schema_check: bool = True
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def get_redis_settings(self) -> RedisSettings:
        return RedisSettings.from_dsn(self.REDIS_URL)

    @property
    def cors_origins(self) -> list[str]:
        if self.API_CORS_ORIGINS:
            return [origin.strip() for origin in self.API_CORS_ORIGINS.split(",") if origin.strip()]
        return [self.API_ORIGIN]


settings = Settings()
