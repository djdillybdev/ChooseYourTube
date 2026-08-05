"""normalize users, shared catalog, and personal state

Revision ID: 20260720_multi_user
Revises: 20260717_category_comment
Create Date: 2026-07-20
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import context, op


revision: str = "20260720_multi_user"
down_revision: str | Sequence[str] | None = "20260717_category_comment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CHANGED_TABLES = (
    "folders",
    "channels",
    "videos",
    "tags",
    "playlists",
    "channel_tags",
    "video_tags",
    "playlist_videos",
    "categories",
    "channel_categories",
    "subscription_imports",
    "subscription_import_candidates",
    "sync_runs",
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _snapshot(bind, metadata: sa.MetaData) -> dict[str, list[dict]]:
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())
    output: dict[str, list[dict]] = {}
    for name in CHANGED_TABLES:
        if name not in existing:
            output[name] = []
            continue
        table = sa.Table(name, metadata, autoload_with=bind)
        output[name] = [dict(row) for row in bind.execute(sa.select(table)).mappings()]
    return output


def _owner_mapper(bind, rows: dict[str, list[dict]]):
    user_ids = {str(value) for value in bind.execute(sa.text("SELECT id FROM users")).scalars()}
    x_args = context.get_x_argument(as_dictionary=True)
    legacy_target = x_args.get("legacy_owner_user_id")
    owners = {
        str(row["owner_id"])
        for table_rows in rows.values()
        for row in table_rows
        if row.get("owner_id") is not None
    }
    if "test-user" in owners:
        if not legacy_target:
            raise RuntimeError(
                "Legacy test-user rows exist; rerun with "
                "-x legacy_owner_user_id=<existing-user-uuid>."
            )
        if legacy_target not in user_ids:
            raise RuntimeError("legacy_owner_user_id does not reference an existing user")

    def resolve(value) -> uuid.UUID:
        raw = str(value)
        if raw == "test-user":
            raw = str(legacy_target)
        try:
            parsed = uuid.UUID(raw)
        except ValueError as exc:
            raise RuntimeError(f"Unrecognized legacy owner_id: {raw}") from exc
        if str(parsed) not in user_ids:
            raise RuntimeError(f"owner_id has no matching users row: {raw}")
        return parsed

    for owner in owners:
        resolve(owner)
    return resolve


def _latest(rows: list[dict], key: str) -> list[dict]:
    def comparable(value):
        if value is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    chosen: dict[object, dict] = {}
    for row in rows:
        identity = row[key]
        current = chosen.get(identity)
        if current is None or comparable(row.get("last_updated")) > comparable(current.get("last_updated")):
            chosen[identity] = row
    for identity, row in chosen.items():
        created = [item.get("created_at") for item in rows if item[key] == identity and item.get("created_at")]
        if created:
            row["created_at"] = min(created)
    return list(chosen.values())


def _drop_old_tables() -> None:
    for name in (
        "channel_categories",
        "channel_tags",
        "video_tags",
        "playlist_videos",
        "sync_runs",
        "subscription_import_candidates",
        "subscription_imports",
        "playlists",
        "categories",
        "tags",
        "videos",
        "channels",
        "folders",
    ):
        op.drop_table(name)


def _create_new_tables(bind):
    from app.db.base import Base
    import app.db.models  # noqa: F401

    order = (
        "folders",
        "channels",
        "user_channels",
        "videos",
        "user_video_states",
        "tags",
        "categories",
        "playlists",
        "channel_tags",
        "channel_categories",
        "video_tags",
        "playlist_videos",
        "subscription_imports",
        "subscription_import_tags",
        "subscription_import_candidates",
        "sync_runs",
    )
    for name in order:
        Base.metadata.tables[name].create(bind, checkfirst=True)
    return Base.metadata


def _insert(bind, table, values: list[dict]) -> None:
    if values:
        bind.execute(sa.insert(table), values)


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(
        "users",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    legacy_metadata = sa.MetaData()
    rows = _snapshot(bind, legacy_metadata)
    owner = _owner_mapper(bind, rows)
    _drop_old_tables()
    metadata = _create_new_tables(bind)

    channels = []
    for row in _latest(rows["channels"], "id"):
        channels.append({key: row.get(key) for key in (
            "id", "title", "handle", "description", "thumbnail_url", "uploads_playlist_id",
            "created_at", "last_updated", "rss_etag", "rss_last_modified"
        )})
    _insert(bind, metadata.tables["channels"], channels)

    folders = []
    for row in rows["folders"]:
        folders.append({
            "id": row["id"], "user_id": owner(row["owner_id"]), "name": row["name"],
            "icon_key": row.get("icon_key"), "position": row.get("position", 0),
            "created_at": row.get("created_at") or _now(), "parent_id": row.get("parent_id"),
        })
    _insert(bind, metadata.tables["folders"], folders)

    user_channels = []
    seen_links = set()
    for row in rows["channels"]:
        uid = owner(row["owner_id"])
        key = (uid, row["id"])
        if key in seen_links:
            raise RuntimeError(f"Conflicting legacy channel ownership for {key}")
        seen_links.add(key)
        user_channels.append({
            "user_id": uid, "channel_id": row["id"], "folder_id": row.get("folder_id"),
            "is_favorited": bool(row.get("is_favorited")),
            "followed_at": row.get("created_at") or _now(),
            "updated_at": row.get("last_updated") or _now(),
        })
    _insert(bind, metadata.tables["user_channels"], user_channels)

    videos = []
    for row in _latest(rows["videos"], "id"):
        videos.append({key: row.get(key) for key in (
            "id", "title", "description", "thumbnail_url", "published_at", "duration_seconds",
            "is_short", "created_at", "last_updated", "yt_tags", "channel_id"
        )})
    _insert(bind, metadata.tables["videos"], videos)

    states = []
    for row in rows["videos"]:
        if row.get("is_favorited") or row.get("is_watched"):
            states.append({
                "user_id": owner(row["owner_id"]), "video_id": row["id"],
                "is_favorited": bool(row.get("is_favorited")),
                "is_watched": bool(row.get("is_watched")),
                "created_at": row.get("created_at") or _now(),
                "updated_at": row.get("last_updated") or _now(),
            })
    _insert(bind, metadata.tables["user_video_states"], states)

    for old_name, new_name, fields in (
        ("tags", "tags", ("id", "name", "created_at")),
        ("categories", "categories", ("id", "name", "normalized_name", "icon_key", "created_at")),
    ):
        values = []
        for row in rows[old_name]:
            item = {key: row.get(key) for key in fields}
            item["user_id"] = owner(row["owner_id"])
            values.append(item)
        _insert(bind, metadata.tables[new_name], values)

    playlists = []
    for row in rows["playlists"]:
        item = {key: row.get(key) for key in (
            "id", "name", "description", "thumbnail_url", "is_system", "system_key", "source_type",
            "source_channel_id", "source_youtube_playlist_id", "source_is_active",
            "source_last_synced_at", "current_position", "created_at"
        )}
        item["user_id"] = owner(row["owner_id"])
        playlists.append(item)
    _insert(bind, metadata.tables["playlists"], playlists)

    for old_name, new_name, id_fields in (
        ("channel_tags", "channel_tags", ("channel_id", "tag_id")),
        ("channel_categories", "channel_categories", ("channel_id", "category_id")),
        ("video_tags", "video_tags", ("video_id", "tag_id")),
        ("playlist_videos", "playlist_videos", ("playlist_id", "video_id", "position")),
    ):
        values = []
        for row in rows[old_name]:
            item = {key: row.get(key) for key in id_fields}
            item["user_id"] = owner(row["owner_id"])
            item["created_at"] = row.get("created_at") or _now()
            values.append(item)
        _insert(bind, metadata.tables[new_name], values)

    imports = []
    import_tags = []
    for row in rows["subscription_imports"]:
        uid = owner(row["owner_id"])
        item = {key: value for key, value in row.items() if key not in {"owner_id", "destination_tag_ids"}}
        item["user_id"] = uid
        imports.append(item)
        raw_tags = row.get("destination_tag_ids") or []
        if isinstance(raw_tags, str):
            raw_tags = json.loads(raw_tags)
        for tag_id in raw_tags:
            import_tags.append({"user_id": uid, "import_id": row["id"], "tag_id": tag_id, "created_at": _now()})
    _insert(bind, metadata.tables["subscription_imports"], imports)
    _insert(bind, metadata.tables["subscription_import_tags"], import_tags)

    candidates = []
    for row in rows["subscription_import_candidates"]:
        candidates.append({key: value for key, value in row.items() if key != "owner_id"})
    _insert(bind, metadata.tables["subscription_import_candidates"], candidates)

    runs = []
    active_refreshes: set[str] = set()
    for row in rows["sync_runs"]:
        item = {key: value for key, value in row.items() if key != "owner_id"}
        item["user_id"] = owner(row["owner_id"])
        is_active_refresh = (
            item.get("kind") == "channel_refresh"
            and item.get("channel_id") is not None
            and item.get("status") in {"queued", "running"}
        )
        if is_active_refresh and item["channel_id"] in active_refreshes:
            now = _now()
            item.update(
                status="failed",
                error_code="MIGRATION_DUPLICATE_ACTIVE_REFRESH",
                error_message="Superseded while merging shared channel refresh jobs.",
                finished_at=now,
                updated_at=now,
            )
        elif is_active_refresh:
            active_refreshes.add(item["channel_id"])
        runs.append(item)
    _insert(bind, metadata.tables["sync_runs"], runs)

    expected_links = len(rows["channels"])
    actual_links = bind.scalar(sa.select(sa.func.count()).select_from(metadata.tables["user_channels"]))
    if actual_links != expected_links:
        raise RuntimeError("user channel count changed during migration")
    expected_states = sum(bool(row.get("is_favorited") or row.get("is_watched")) for row in rows["videos"])
    actual_states = bind.scalar(sa.select(sa.func.count()).select_from(metadata.tables["user_video_states"]))
    if actual_states != expected_states:
        raise RuntimeError("video state count changed during migration")


def downgrade() -> None:
    raise RuntimeError(
        "This normalization migration is data-shape destructive. Restore the pre-upgrade "
        "database snapshot before deploying the previous application version."
    )
