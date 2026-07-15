from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text

from scripts import verify_migration_head


def _database_url(path: Path) -> str:
    return f"sqlite:///{path}"


def _record_heads(database_url: str, heads: set[str]) -> None:
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE alembic_version ("
                    "version_num VARCHAR(32) NOT NULL PRIMARY KEY)"
                )
            )
            for head in heads:
                connection.execute(
                    text("INSERT INTO alembic_version (version_num) VALUES (:head)"),
                    {"head": head},
                )
    finally:
        engine.dispose()


def test_main_accepts_database_at_repository_head(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    config = verify_migration_head.build_alembic_config()
    database_url = _database_url(tmp_path / "current.sqlite")
    expected = verify_migration_head.expected_heads(config)
    _record_heads(database_url, expected)
    monkeypatch.setenv("ALEMBIC_DATABASE_URL", database_url)

    assert verify_migration_head.main() == 0
    assert "Migration heads verified" in capsys.readouterr().out


def test_main_rejects_stale_database_head(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    database_url = _database_url(tmp_path / "stale.sqlite")
    _record_heads(database_url, {"stale_revision"})
    monkeypatch.setenv("ALEMBIC_DATABASE_URL", database_url)

    assert verify_migration_head.main() == 1
    output = capsys.readouterr().err
    assert "Migration head mismatch" in output
    assert "stale_revision" in output


def test_main_rejects_database_without_version_table(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    database_url = _database_url(tmp_path / "unversioned.sqlite")
    engine = create_engine(database_url)
    engine.dispose()
    monkeypatch.setenv("ALEMBIC_DATABASE_URL", database_url)

    assert verify_migration_head.main() == 1
    assert "current=[]" in capsys.readouterr().err


def test_main_reports_connection_failure_without_exposing_credentials(
    monkeypatch,
    capsys,
) -> None:
    database_url = "postgresql+psycopg2://user:secret-password@localhost/database"
    monkeypatch.setenv("ALEMBIC_DATABASE_URL", database_url)

    def fail_to_connect(_: str) -> set[str]:
        raise ConnectionError(database_url)

    monkeypatch.setattr(verify_migration_head, "current_heads", fail_to_connect)

    assert verify_migration_head.main() == 1
    output = capsys.readouterr().err
    assert "ConnectionError" in output
    assert "secret-password" not in output


def test_database_url_resolution_matches_migration_environment() -> None:
    config = verify_migration_head.build_alembic_config()
    config.set_main_option("sqlalchemy.url", "sqlite:///configured.sqlite")

    assert (
        verify_migration_head.resolve_database_url(
            config,
            {
                "ALEMBIC_DATABASE_URL": "sqlite:///alembic.sqlite",
                "DATABASE_URL": "sqlite:///application.sqlite",
            },
        )
        == "sqlite:///alembic.sqlite"
    )
    assert (
        verify_migration_head.resolve_database_url(
            config,
            {"DATABASE_URL": "sqlite:///application.sqlite"},
        )
        == "sqlite:///application.sqlite"
    )
    assert verify_migration_head.resolve_database_url(config, {}) == (
        "sqlite:///configured.sqlite"
    )


def test_asyncpg_database_url_is_converted_to_sync_driver() -> None:
    assert verify_migration_head.sync_database_url(
        "postgresql+asyncpg://user:password@localhost/database"
    ) == "postgresql+psycopg2://user:password@localhost/database"
