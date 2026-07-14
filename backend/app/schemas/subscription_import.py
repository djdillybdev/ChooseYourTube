from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from .base import BaseSchema, PaginatedResponse


class SubscriptionImportSource(StrEnum):
    YOUTUBE_OAUTH = "youtube_oauth"
    YOUTUBE_TAKEOUT_CSV = "youtube_takeout_csv"


class SubscriptionImportStatus(StrEnum):
    COLLECTING = "collecting"
    READY = "ready"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


class SubscriptionCandidateState(StrEnum):
    NEW = "new"
    EXISTING = "existing"
    INVALID = "invalid"
    SELECTED = "selected"
    IMPORTED = "imported"
    FAILED = "failed"


class SubscriptionImportOut(BaseSchema):
    id: uuid.UUID
    source: SubscriptionImportSource
    status: SubscriptionImportStatus
    candidate_count: int
    new_count: int
    existing_count: int
    invalid_count: int
    selected_count: int
    imported_count: int
    failed_count: int
    destination_folder_id: str | None
    destination_tag_ids: list[str]
    error_code: str | None
    error_message: str | None
    created_at: datetime
    ready_at: datetime | None
    queued_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    updated_at: datetime


class SubscriptionImportCandidateOut(BaseSchema):
    id: uuid.UUID
    channel_id: str | None
    channel_title: str | None
    channel_url: str | None
    state: SubscriptionCandidateState
    source_index: int
    message: str | None


class SubscriptionImportDetailOut(BaseModel):
    import_: SubscriptionImportOut = Field(alias="import", serialization_alias="import")
    candidates: PaginatedResponse[SubscriptionImportCandidateOut]


class CandidateSelectionUpdate(BaseModel):
    candidate_ids: list[uuid.UUID] = Field(min_length=1, max_length=5000)
    selected: bool


class SubscriptionImportCommit(BaseModel):
    selected_candidate_ids: list[uuid.UUID] | None = Field(default=None, max_length=5000)
    folder_id: str | None = None
    tag_ids: list[str] = Field(default_factory=list, max_length=200)


class OAuthStartOut(BaseModel):
    import_id: uuid.UUID
    authorization_url: str
