from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


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
        UniqueConstraint("owner_id", "id", name="uq_subscription_import_owner_id"),
        Index("ix_subscription_imports_owner_created", "owner_id", "created_at"),
        Index("ix_subscription_imports_status", "owner_id", "status"),
        Index(
            "ix_subscription_imports_oauth_state",
            "oauth_state_hash",
            unique=True,
            postgresql_where=text("oauth_state_hash IS NOT NULL"),
            sqlite_where=text("oauth_state_hash IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
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
    destination_tag_ids: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON), nullable=False, default=list
    )
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


class SubscriptionImportCandidate(Base):
    __tablename__ = "subscription_import_candidates"
    __table_args__ = (
        CheckConstraint(
            "state IN ('new', 'existing', 'invalid', 'selected', 'imported', 'failed')",
            name="ck_subscription_import_candidates_state",
        ),
        ForeignKeyConstraint(
            ["owner_id", "import_id"],
            ["subscription_imports.owner_id", "subscription_imports.id"],
            ondelete="CASCADE",
            name="fk_subscription_import_candidates_import",
        ),
        UniqueConstraint("import_id", "source_index", name="uq_import_candidate_source_index"),
        Index("ix_import_candidates_import_state", "owner_id", "import_id", "state"),
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
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
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
