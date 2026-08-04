from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import StrEnum

from pydantic import field_validator

from .base import BaseSchema


class SyncRunKind(StrEnum):
    INITIAL_CHANNEL_SYNC = "initial_channel_sync"
    CHANNEL_REFRESH = "channel_refresh"
    PLAYLIST_SYNC = "playlist_sync"
    SUBSCRIPTION_IMPORT = "subscription_import"
    DEMO_MAINTENANCE = "demo_maintenance"


class SyncRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


TERMINAL_SYNC_STATUSES = {
    SyncRunStatus.SUCCEEDED,
    SyncRunStatus.PARTIAL,
    SyncRunStatus.FAILED,
}


class SyncRunOut(BaseSchema):
    id: uuid.UUID
    owner_id: str
    kind: SyncRunKind
    status: SyncRunStatus
    channel_id: str | None
    subscription_import_id: uuid.UUID | None
    attempt_count: int
    max_attempts: int
    items_discovered: int
    items_created: int
    items_updated: int
    items_skipped: int
    items_failed: int
    error_code: str | None
    error_message: str | None
    retryable: bool = False
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    next_retry_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_validator("owner_id", mode="before")
    @classmethod
    def serialize_owner_id(cls, value: object) -> object:
        if isinstance(value, uuid.UUID):
            return str(value)
        return value


class LatestSyncSummary(BaseSchema):
    id: uuid.UUID
    kind: SyncRunKind
    status: SyncRunStatus
    error_code: str | None
    error_message: str | None
    retryable: bool = False
    queued_at: datetime
    finished_at: datetime | None
    last_successful_at: datetime | None = None


class YouTubeQuotaStatusOut(BaseSchema):
    date: date
    budget: int
    estimated_units_used: int
    estimated_units_remaining: int
    call_count: int
    exhausted: bool
