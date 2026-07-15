"""PostgreSQL migration smoke tests used by CI.

The database URL must point at a disposable database dedicated to this test.
"""

from __future__ import annotations

import os

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text


MIGRATION_TEST_DATABASE_URL = os.getenv("MIGRATION_TEST_DATABASE_URL")
PRE_PORTFOLIO_REVISION = "20260305_refresh_sessions"


def _config() -> Config:
    assert MIGRATION_TEST_DATABASE_URL is not None
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", MIGRATION_TEST_DATABASE_URL)
    return config


def _reset_database() -> None:
    assert MIGRATION_TEST_DATABASE_URL is not None
    engine = create_engine(MIGRATION_TEST_DATABASE_URL)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    engine.dispose()


def _assert_at_head(config: Config) -> None:
    assert MIGRATION_TEST_DATABASE_URL is not None
    expected = set(ScriptDirectory.from_config(config).get_heads())
    engine = create_engine(MIGRATION_TEST_DATABASE_URL)
    with engine.connect() as connection:
        current = {row[0] for row in connection.execute(text("SELECT version_num FROM alembic_version"))}
    engine.dispose()
    assert current == expected


@pytest.mark.integration
@pytest.mark.skipif(
    MIGRATION_TEST_DATABASE_URL is None,
    reason="MIGRATION_TEST_DATABASE_URL is required for destructive migration tests",
)
def test_upgrade_empty_postgres_database_to_head() -> None:
    config = _config()
    _reset_database()
    command.upgrade(config, "head")
    _assert_at_head(config)


@pytest.mark.integration
@pytest.mark.skipif(
    MIGRATION_TEST_DATABASE_URL is None,
    reason="MIGRATION_TEST_DATABASE_URL is required for destructive migration tests",
)
def test_upgrade_pre_portfolio_schema_to_head() -> None:
    config = _config()
    _reset_database()
    command.upgrade(config, PRE_PORTFOLIO_REVISION)
    command.upgrade(config, "head")
    _assert_at_head(config)
