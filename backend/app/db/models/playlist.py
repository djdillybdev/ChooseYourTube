from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime, timezone
import uuid

import sqlalchemy as sa
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Boolean,
    Integer,
    Index,
    ForeignKeyConstraint,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym, validates
from ..base import Base
from ..tenancy import user_uuid
from .association_tables import playlist_videos

if TYPE_CHECKING:
    from .channel import Channel
    from .video import Video


class Playlist(Base):
    __tablename__ = "playlists"
    __table_args__ = (
        UniqueConstraint("user_id", "id", name="uq_playlist_user_id"),
        UniqueConstraint(
            "user_id",
            "source_type",
            "source_youtube_playlist_id",
            name="uq_playlist_user_source_playlist",
        ),
        ForeignKeyConstraint(
            ["user_id", "source_channel_id"],
            ["user_channels.user_id", "user_channels.channel_id"],
            ondelete="CASCADE",
        ),
        Index(
            "uq_playlist_owner_system_key",
            "user_id",
            "system_key",
            unique=True,
            postgresql_where=sa.text("system_key IS NOT NULL"),
            sqlite_where=sa.text("system_key IS NOT NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, comment="UUID as string"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner_id = synonym("user_id")

    @validates("user_id")
    def _validate_user_id(self, key, value):
        return user_uuid(value)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    system_key: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="manual"
    )
    source_channel_id: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )
    source_youtube_playlist_id: Mapped[str | None] = mapped_column(
        String(48), nullable=True, index=True
    )
    source_is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    source_last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_position: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Many-to-many relationship with Videos
    videos: Mapped[list["Video"]] = relationship(
        secondary=playlist_videos,
        primaryjoin="and_(Playlist.user_id == playlist_videos.c.user_id, Playlist.id == playlist_videos.c.playlist_id)",
        secondaryjoin="Video.id == playlist_videos.c.video_id",
        lazy="selectin",
    )
    source_channel: Mapped["Channel | None"] = relationship(
        secondary="user_channels", viewonly=True, lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Playlist(id={self.id}, name='{self.name}')>"
