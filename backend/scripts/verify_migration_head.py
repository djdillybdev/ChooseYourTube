"""Verify that a database is at every Alembic migration head."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def build_alembic_config() -> Config:
    """Load Alembic configuration independently of the current directory."""
    return Config(str(BACKEND_ROOT / "alembic.ini"))


def sync_database_url(url: str) -> str:
    """Convert the application's async PostgreSQL URL for sync migration tools."""
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    return url


def resolve_database_url(
    config: Config,
    environ: Mapping[str, str] = os.environ,
) -> str:
    """Resolve the database URL with the same precedence as migration/env.py."""
    configured = config.get_main_option("sqlalchemy.url")
    url = (
        environ.get("ALEMBIC_DATABASE_URL")
        or environ.get("DATABASE_URL")
        or configured
    )
    if not url:
        raise RuntimeError("No database URL is configured")
    return sync_database_url(url)


def expected_heads(config: Config) -> set[str]:
    """Return all migration heads defined by the repository."""
    return set(ScriptDirectory.from_config(config).get_heads())


def current_heads(database_url: str) -> set[str]:
    """Return all migration heads recorded in the target database."""
    engine = create_engine(database_url, poolclass=NullPool)
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            return set(context.get_current_heads())
    finally:
        engine.dispose()


def verify_migration_head(config: Config, database_url: str) -> bool:
    """Compare database heads with repository heads without exposing the URL."""
    expected = expected_heads(config)
    current = current_heads(database_url)
    if current != expected:
        print(
            "Migration head mismatch: "
            f"current={sorted(current)} expected={sorted(expected)}",
            file=sys.stderr,
        )
        return False

    print(f"Migration heads verified: {sorted(current)}")
    return True


def main() -> int:
    config = build_alembic_config()
    try:
        database_url = resolve_database_url(config)
        return 0 if verify_migration_head(config, database_url) else 1
    except Exception as exc:
        print(
            f"Migration head verification failed: {type(exc).__name__}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
