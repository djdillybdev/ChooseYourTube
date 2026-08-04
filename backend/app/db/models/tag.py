from __future__ import annotations
from datetime import datetime, timezone
import uuid

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, synonym, validates
from ..base import Base
from ..tenancy import user_uuid
class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("user_id", "id", name="uq_tag_user_id"),
        UniqueConstraint("user_id", "name", name="uq_tag_user_name"),
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
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __init__(self, **kwargs):
        """Initialize Tag and normalize name to lowercase for case-insensitive storage."""
        if "name" in kwargs:
            kwargs["name"] = kwargs["name"].lower()
        super().__init__(**kwargs)
