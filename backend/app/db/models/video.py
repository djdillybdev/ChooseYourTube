from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .channel import Channel
    from .user_state import UserVideoState


class Video(Base):
    __tablename__ = "videos"
    __allow_unmapped__ = True

    is_favorited: bool
    is_watched: bool
    tags: list[Any]
    tag_ids: list[str]
    user_state: Any
    __table_args__ = (
        Index("ix_video_is_short", "is_short"),
        Index("ix_video_channel_published", "channel_id", "published_at"),
        Index("ix_video_duration", "duration_seconds"),
    )

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    is_short: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    yt_tags: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON), default=list, nullable=False, server_default="[]"
    )
    channel_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True
    )

    channel: Mapped["Channel"] = relationship(back_populates="videos")
    user_states: Mapped[list["UserVideoState"]] = relationship(
        back_populates="video", cascade="all, delete-orphan", lazy="noload"
    )

    def __init__(self, **kwargs):
        owner_id = kwargs.pop("owner_id", None)
        favorite = kwargs.pop("is_favorited", False)
        watched = kwargs.pop("is_watched", False)
        tags = kwargs.pop("tags", None)
        super().__init__(**kwargs)
        self.is_favorited = favorite
        self.is_watched = watched
        self.tags = list(tags or [])
        self.tag_ids = [tag.id for tag in self.tags]
        self.user_state = None
        if owner_id is not None and (favorite or watched):
            from ..tenancy import user_uuid
            from .user_state import UserVideoState

            state = UserVideoState(
                user_id=user_uuid(owner_id),
                video_id=self.id,
                is_favorited=favorite,
                is_watched=watched,
            )
            self.user_states = [state]
            self.user_state = state

    def __repr__(self) -> str:
        return f"<Video(id={self.id}, title='{self.title}')>"
