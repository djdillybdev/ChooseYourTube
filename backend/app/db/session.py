import contextlib
from typing import Any, AsyncIterator

from ..core.config import settings
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

# Heavily inspired by https://praciano.com.br/fastapi-and-async-sqlalchemy-20-with-pytest-done-right.html


class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any] = {}):
        self._assert_async_driver(host)
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            autocommit=False, bind=self._engine, expire_on_commit=False
        )

    @staticmethod
    def _assert_async_driver(host: str) -> None:
        """Reject runtime database URLs that cannot back an async SQLAlchemy engine."""
        try:
            dialect = make_url(host).get_dialect()
        except Exception:
            raise ValueError(
                "DATABASE_URL must use a supported async SQLAlchemy driver; "
                "use postgresql+asyncpg:// for PostgreSQL."
            ) from None

        if not dialect.is_async:
            raise ValueError(
                "DATABASE_URL must use an async SQLAlchemy driver; "
                "use postgresql+asyncpg:// for PostgreSQL."
            )

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def engine_kwargs_for_runtime() -> dict[str, Any]:
    """Use Neon/PgBouncer as the only pool in ephemeral serverless functions."""
    kwargs: dict[str, Any] = {"echo": settings.echo_sql}
    if settings.DATABASE_POOL_MODE == "serverless":
        kwargs["poolclass"] = NullPool
    else:
        kwargs["pool_pre_ping"] = True
        kwargs["pool_recycle"] = 300
    return kwargs


sessionmanager = DatabaseSessionManager(
    settings.DATABASE_URL, engine_kwargs_for_runtime()
)


async def get_db_session():
    async with sessionmanager.session() as session:
        yield session
