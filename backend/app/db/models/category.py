from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, synonym, validates

from ..base import Base
from ..tenancy import user_uuid
class Category(Base):
    __tablename__ = "categories"
    __allow_unmapped__ = True
    channels: list[Any]
    __table_args__ = (
        UniqueConstraint("user_id", "id", name="uq_category_user_id"),
        UniqueConstraint(
            "user_id", "normalized_name", name="uq_category_user_normalized_name"
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
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    icon_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"
