from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, UniqueConstraint, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from .association_tables import channel_categories

if TYPE_CHECKING:
    from .channel import Channel


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("owner_id", "id", name="uq_category_owner_id"),
        UniqueConstraint(
            "owner_id", "normalized_name", name="uq_category_owner_normalized_name"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, index=True, comment="UUID as string"
    )
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    icon_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    channels: Mapped[list["Channel"]] = relationship(
        secondary=channel_categories,
        primaryjoin=and_(
            owner_id == channel_categories.c.owner_id,
            id == channel_categories.c.category_id,
        ),
        secondaryjoin="and_(Channel.owner_id == channel_categories.c.owner_id, Channel.id == channel_categories.c.channel_id)",
        back_populates="categories",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"
