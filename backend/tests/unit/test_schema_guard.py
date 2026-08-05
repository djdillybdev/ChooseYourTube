"""Tests for schema drift guard."""

import pytest

from app.db.schema_guard import (
    REQUIRED_PLAYLIST_COLUMNS,
    REQUIRED_IMPORT_COLUMNS,
    REQUIRED_USER_STATE_COLUMNS,
    SchemaMismatchError,
    assert_required_playlist_schema,
)


@pytest.mark.asyncio
async def test_assert_required_playlist_schema_passes_when_columns_exist(
    db_session, monkeypatch
):
    async def fake_get_table_columns(_db_session, table_name):
        if table_name == "playlists":
            return set(REQUIRED_PLAYLIST_COLUMNS)
        expected = {**REQUIRED_IMPORT_COLUMNS, **REQUIRED_USER_STATE_COLUMNS}
        return set(expected[table_name])

    monkeypatch.setattr("app.db.schema_guard._get_table_columns", fake_get_table_columns)

    await assert_required_playlist_schema(db_session)


@pytest.mark.asyncio
async def test_assert_required_playlist_schema_raises_when_columns_missing(
    db_session, monkeypatch
):
    async def fake_get_table_columns(_db_session, _table_name):
        return {"id", "name", "description"}

    monkeypatch.setattr("app.db.schema_guard._get_table_columns", fake_get_table_columns)

    with pytest.raises(SchemaMismatchError) as exc:
        await assert_required_playlist_schema(db_session)

    message = str(exc.value)
    assert "playlists" in message
    assert "alembic upgrade head" in message
    assert "thumbnail_url" in message
