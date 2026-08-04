from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    ForeignKey,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym, validates

from ..base import Base
from ..tenancy import user_uuid
from .association_tables import subscription_import_tags

if TYPE_CHECKING:
    from .tag import Tag


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SubscriptionImport(Base):
    __tablename__ = "subscription_imports"
    __table_args__ = (
        CheckConstraint(
            "source IN ('youtube_oauth', 'youtube_takeout_csv')",
            name="ck_subscription_imports_source",
        ),
        CheckConstraint(
            "status IN ('collecting', 'ready', 'queued', 'running', "
            "'succeeded', 'partial', 'failed')",
            name="ck_subscription_imports_status",
        ),
        UniqueConstraint("user_id", "id", name="uq_subscription_import_user_id"),
        Index("ix_subscription_imports_user_created", "user_id", "created_at"),
        Index("ix_subscription_imports_status", "user_id", "status"),
        Index(
            "ix_subscription_imports_oauth_state",
            "oauth_state_hash",
            unique=True,
            postgresql_where=text("oauth_state_hash IS NOT NULL"),
            sqlite_where=text("oauth_state_hash IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    owner_id = synonym("user_id")

    @validates("user_id")
    def _validate_user_id(self, key, value):
        return user_uuid(value)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="collecting")

    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    existing_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    invalid_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    selected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    imported_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    destination_folder_id: Mapped[str | None] = mapped_column(String(36))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)

    oauth_state_hash: Mapped[str | None] = mapped_column(String(64))
    oauth_state_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    oauth_state_consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    candidates: Mapped[list[SubscriptionImportCandidate]] = relationship(
        back_populates="subscription_import", cascade="all, delete-orphan", lazy="noload"
    )
    sync_runs = relationship(
        "SyncRun",
        back_populates="subscription_import",
        lazy="noload",
        overlaps="channel,sync_runs",
    )
    destination_tags: Mapped[list["Tag"]] = relationship(
        secondary=subscription_import_tags, lazy="selectin"
    )

    @property
    def destination_tag_ids(self) -> list[str]:
        return [tag.id for tag in self.destination_tags]


class SubscriptionImportCandidate(Base):
    __tablename__ = "subscription_import_candidates"
    __table_args__ = (
        CheckConstraint(
            "state IN ('new', 'existing', 'invalid', 'selected', 'imported', 'failed')",
            name="ck_subscription_import_candidates_state",
        ),
        ForeignKeyConstraint(
            ["import_id"],
            ["subscription_imports.id"],
            ondelete="CASCADE",
            name="fk_subscription_import_candidates_import",
        ),
        UniqueConstraint("import_id", "source_index", name="uq_import_candidate_source_index"),
        Index("ix_import_candidates_import_state", "import_id", "state"),
        Index(
            "uq_import_candidates_channel",
            "import_id",
            "channel_id",
            unique=True,
            postgresql_where=text("channel_id IS NOT NULL"),
            sqlite_where=text("channel_id IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    import_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    channel_id: Mapped[str | None] = mapped_column(String(32))
    channel_title: Mapped[str | None] = mapped_column(String(255))
    channel_url: Mapped[str | None] = mapped_column(String(512))
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    source_index: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    subscription_import: Mapped[SubscriptionImport] = relationship(back_populates="candidates")
