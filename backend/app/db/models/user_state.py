from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, ForeignKeyConstraint, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .channel import Channel
    from .folder import Folder
    from .video import Video


class UserChannel(Base):
    __tablename__ = "user_channels"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "folder_id"],
            ["folders.user_id", "folders.id"],
            ondelete="RESTRICT",
            name="fk_user_channels_folder",
        ),
        Index("ix_user_channels_folder", "user_id", "folder_id"),
        Index("ix_user_channels_favorite", "user_id", "is_favorited"),
        Index("ix_user_channels_channel", "channel_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    channel_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("channels.id", ondelete="CASCADE"), primary_key=True
    )
    folder_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    is_favorited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    followed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    channel: Mapped["Channel"] = relationship(back_populates="user_links")
    folder: Mapped["Folder | None"] = relationship(back_populates="channel_links")


class UserVideoState(Base):
    __tablename__ = "user_video_states"
    __table_args__ = (
        Index("ix_user_video_states_video", "video_id"),
        Index("ix_user_video_states_watched", "user_id", "is_watched"),
        Index("ix_user_video_states_favorite", "user_id", "is_favorited"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    video_id: Mapped[str] = mapped_column(
        String(16), ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True
    )
    is_favorited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_watched: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    video: Mapped["Video"] = relationship(back_populates="user_states")
