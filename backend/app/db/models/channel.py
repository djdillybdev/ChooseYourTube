from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

from sqlalchemy import DateTime, String, Text, func, select
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from ..base import Base
from .video import Video

if TYPE_CHECKING:
    from .user_state import UserChannel
    from .sync_run import SyncRun


class Channel(Base):
    __tablename__ = "channels"
    __allow_unmapped__ = True

    is_favorited: bool
    folder_id: str | None
    followed_at: datetime
    tags: list[Any]
    tag_ids: list[str]
    user_link: Any

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    handle: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    uploads_playlist_id: Mapped[str] = mapped_column(String(48), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    rss_etag: Mapped[str | None] = mapped_column(String(512), nullable=True)
    rss_last_modified: Mapped[str | None] = mapped_column(String(128), nullable=True)

    videos: Mapped[list["Video"]] = relationship(
        back_populates="channel", cascade="all, delete-orphan", lazy="select"
    )
    user_links: Mapped[list["UserChannel"]] = relationship(
        back_populates="channel", cascade="all, delete-orphan", lazy="noload"
    )
    sync_runs: Mapped[list["SyncRun"]] = relationship(back_populates="channel", lazy="noload")

    def __init__(self, **kwargs):
        owner_id = kwargs.pop("owner_id", None)
        favorite = kwargs.pop("is_favorited", False)
        folder_id = kwargs.pop("folder_id", None)
        tags = kwargs.pop("tags", None)
        followed_at = kwargs.get("created_at")
        super().__init__(**kwargs)
        self.is_favorited = favorite
        self.folder_id = folder_id
        self.tags = list(tags or [])
        self.tag_ids = [tag.id for tag in self.tags]
        if owner_id is not None:
            from ..tenancy import user_uuid
            from .user_state import UserChannel

            link = UserChannel(
                user_id=user_uuid(owner_id),
                channel_id=self.id,
                folder_id=folder_id,
                is_favorited=favorite,
                **({"followed_at": followed_at} if followed_at is not None else {}),
            )
            self.user_links = [link]
            self.user_link = link

    def __repr__(self) -> str:
        return f"<Channel(id={self.id}, title='{self.title}')>"


Channel.total_videos = column_property(
    select(func.count(Video.id))
    .where(Video.channel_id == Channel.id)
    .correlate_except(Video)
    .scalar_subquery()
)
