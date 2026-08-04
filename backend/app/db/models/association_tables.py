"""Tenant-aware association tables for user-owned organization."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, ForeignKeyConstraint, Integer, Table, Uuid, String, UniqueConstraint

from ..base import Base


def _created_at() -> Column:
    return Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


channel_tags = Table(
    "channel_tags",
    Base.metadata,
    Column("user_id", Uuid, primary_key=True, nullable=False),
    Column("channel_id", String(32), primary_key=True, nullable=False),
    Column("tag_id", String(36), primary_key=True, nullable=False),
    _created_at(),
    ForeignKeyConstraint(
        ["user_id", "channel_id"],
        ["user_channels.user_id", "user_channels.channel_id"],
        ondelete="CASCADE",
        name="fk_channel_tags_user_channel",
    ),
    ForeignKeyConstraint(
        ["user_id", "tag_id"],
        ["tags.user_id", "tags.id"],
        ondelete="CASCADE",
        name="fk_channel_tags_tag",
    ),
)

channel_categories = Table(
    "channel_categories",
    Base.metadata,
    Column("user_id", Uuid, primary_key=True, nullable=False),
    Column("channel_id", String(32), primary_key=True, nullable=False),
    Column("category_id", String(36), primary_key=True, nullable=False),
    _created_at(),
    ForeignKeyConstraint(
        ["user_id", "channel_id"],
        ["user_channels.user_id", "user_channels.channel_id"],
        ondelete="CASCADE",
        name="fk_channel_categories_user_channel",
    ),
    ForeignKeyConstraint(
        ["user_id", "category_id"],
        ["categories.user_id", "categories.id"],
        ondelete="CASCADE",
        name="fk_channel_categories_category",
    ),
)

video_tags = Table(
    "video_tags",
    Base.metadata,
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("video_id", String(16), ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(36), primary_key=True, nullable=False),
    _created_at(),
    ForeignKeyConstraint(
        ["user_id", "tag_id"],
        ["tags.user_id", "tags.id"],
        ondelete="CASCADE",
        name="fk_video_tags_tag",
    ),
)

playlist_videos = Table(
    "playlist_videos",
    Base.metadata,
    Column("user_id", Uuid, primary_key=True, nullable=False),
    Column("playlist_id", String(36), primary_key=True, nullable=False),
    Column("video_id", String(16), ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True),
    Column("position", Integer, nullable=False, default=0),
    _created_at(),
    ForeignKeyConstraint(
        ["user_id", "playlist_id"],
        ["playlists.user_id", "playlists.id"],
        ondelete="CASCADE",
        name="fk_playlist_videos_playlist",
    ),
    UniqueConstraint("user_id", "playlist_id", "position", name="uq_playlist_video_position"),
)

subscription_import_tags = Table(
    "subscription_import_tags",
    Base.metadata,
    Column("user_id", Uuid, primary_key=True, nullable=False),
    Column("import_id", Uuid, primary_key=True, nullable=False),
    Column("tag_id", String(36), primary_key=True, nullable=False),
    _created_at(),
    ForeignKeyConstraint(
        ["user_id", "import_id"],
        ["subscription_imports.user_id", "subscription_imports.id"],
        ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
        ["user_id", "tag_id"], ["tags.user_id", "tags.id"], ondelete="CASCADE"
    ),
)
