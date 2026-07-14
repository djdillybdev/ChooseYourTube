"""Startup schema drift checks for critical runtime queries."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

REQUIRED_PLAYLIST_COLUMNS: tuple[str, ...] = (
    "system_key",
    "thumbnail_url",
    "source_type",
    "source_channel_id",
    "source_youtube_playlist_id",
    "source_is_active",
    "source_last_synced_at",
)
REQUIRED_IMPORT_COLUMNS: dict[str, tuple[str, ...]] = {
    "subscription_imports": ("id", "owner_id", "source", "status"),
    "subscription_import_candidates": (
        "id",
        "import_id",
        "owner_id",
        "channel_id",
        "state",
    ),
}


class SchemaMismatchError(RuntimeError):
    """Raised when the live database schema is missing required columns."""


async def _get_table_columns(db_session: AsyncSession, table_name: str) -> set[str]:
    bind = db_session.get_bind()
    dialect_name = bind.dialect.name if bind is not None else None

    if dialect_name == "sqlite":
        result = await db_session.execute(text(f"PRAGMA table_info('{table_name}')"))
        # SQLite PRAGMA table_info rows: cid, name, type, notnull, dflt_value, pk
        return {row[1] for row in result.fetchall()}

    result = await db_session.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = :table_name
            """
        ),
        {"table_name": table_name},
    )
    return {row[0] for row in result.fetchall()}


async def assert_required_playlist_schema(db_session: AsyncSession) -> None:
    required = {"playlists": REQUIRED_PLAYLIST_COLUMNS, **REQUIRED_IMPORT_COLUMNS}
    for table_name, expected_columns in required.items():
        columns = await _get_table_columns(db_session, table_name)
        missing = sorted(set(expected_columns) - columns)
        if missing:
            missing_csv = ", ".join(missing)
            raise SchemaMismatchError(
                f"Database schema mismatch for table '{table_name}'. "
                f"Missing required columns: {missing_csv}. "
                "Run `alembic upgrade head` before starting the API."
            )
