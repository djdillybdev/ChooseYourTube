from __future__ import annotations
from typing import TYPE_CHECKING
import uuid
from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime, ForeignKey, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym, validates
from ..base import Base
from ..tenancy import user_uuid

if TYPE_CHECKING:
    from .user_state import UserChannel


class Folder(Base):
    __tablename__ = "folders"
    __table_args__ = (
        UniqueConstraint("user_id", "id", name="uq_folder_user_id"),
        ForeignKeyConstraint(
            ["user_id", "parent_id"],
            ["folders.user_id", "folders.id"],
            ondelete="RESTRICT",
            name="fk_folders_parent",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, index=True, comment="UUID as string"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner_id = synonym("user_id")

    @validates("user_id")
    def _validate_user_id(self, key, value):
        return user_uuid(value)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    icon_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # --- Relationships ---

    # Self-referencing relationship for sub-folders
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Relationship to Parent (Many-to-One to itself)
    # The `remote_side=[id]` is crucial for SQLAlchemy to understand how to join a table to itself.
    parent: Mapped["Folder"] = relationship(back_populates="children", remote_side=[id])

    # Relationship to Children (One-to-Many to itself)
    children: Mapped[list["Folder"]] = relationship(
        back_populates="parent", passive_deletes="all"
    )

    # Relationship to Channels (One-to-Many)
    # A Folder can contain many Channels.
    channel_links: Mapped[list["UserChannel"]] = relationship(back_populates="folder")

    def __repr__(self) -> str:
        return f"<Folder(id={self.id}, name='{self.name}')>"
