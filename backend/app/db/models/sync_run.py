from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym, validates

from ..base import Base
from ..tenancy import user_uuid


ACTIVE_REFRESH_PREDICATE = (
    "status IN ('queued', 'running') AND channel_id IS NOT NULL "
    "AND kind = 'channel_refresh'"
)
ACTIVE_USER_SYNC_PREDICATE = (
    "status IN ('queued', 'running') AND channel_id IS NOT NULL "
    "AND kind IN ('initial_channel_sync', 'playlist_sync')"
)
ACTIVE_IMPORT_PREDICATE = (
    "status IN ('queued', 'running') AND subscription_import_id IS NOT NULL"
)


class SyncRun(Base):
    __tablename__ = "sync_runs"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('initial_channel_sync', 'channel_refresh', 'playlist_sync', "
            "'subscription_import', 'demo_maintenance')",
            name="ck_sync_runs_kind",
        ),
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'partial', 'failed')",
            name="ck_sync_runs_status",
        ),
        ForeignKeyConstraint(
            ["channel_id"],
            ["channels.id"],
            name="fk_sync_runs_channel",
            ondelete="CASCADE",
        ),
        Index("ix_sync_runs_user_queued", "user_id", "queued_at"),
        Index("ix_sync_runs_status", "status"),
        Index("ix_sync_runs_channel", "channel_id"),
        Index("ix_sync_runs_import", "user_id", "subscription_import_id"),
        Index(
            "uq_sync_runs_active_channel_refresh",
            "channel_id",
            "kind",
            unique=True,
            postgresql_where=text(ACTIVE_REFRESH_PREDICATE),
            sqlite_where=text(ACTIVE_REFRESH_PREDICATE),
        ),
        Index(
            "uq_sync_runs_active_user_channel_kind",
            "user_id",
            "channel_id",
            "kind",
            unique=True,
            postgresql_where=text(ACTIVE_USER_SYNC_PREDICATE),
            sqlite_where=text(ACTIVE_USER_SYNC_PREDICATE),
        ),
        Index(
            "uq_sync_runs_active_import_kind",
            "user_id",
            "subscription_import_id",
            "kind",
            unique=True,
            postgresql_where=text(ACTIVE_IMPORT_PREDICATE),
            sqlite_where=text(ACTIVE_IMPORT_PREDICATE),
        ),
        ForeignKeyConstraint(
            ["user_id", "subscription_import_id"],
            ["subscription_imports.user_id", "subscription_imports.id"],
            name="fk_sync_runs_subscription_import",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    owner_id = synonym("user_id")

    @validates("user_id")
    def _validate_user_id(self, key, value):
        return user_uuid(value) if value is not None else None
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="queued", server_default="queued"
    )
    channel_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    subscription_import_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    items_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    queued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    channel = relationship("Channel", back_populates="sync_runs")
    subscription_import = relationship(
        "SubscriptionImport", back_populates="sync_runs", overlaps="channel,sync_runs"
    )


class YouTubeAPIUsage(Base):
    __tablename__ = "youtube_api_usage"
    __table_args__ = (
        UniqueConstraint(
            "usage_date", "operation", "outcome", name="uq_youtube_usage_bucket"
        ),
        CheckConstraint("estimated_units >= 0", name="ck_youtube_usage_units"),
        CheckConstraint("call_count >= 0", name="ck_youtube_usage_calls"),
        Index("ix_youtube_usage_date", "usage_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usage_date: Mapped[date] = mapped_column(Date, nullable=False)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(24), nullable=False)
    estimated_units: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    call_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
