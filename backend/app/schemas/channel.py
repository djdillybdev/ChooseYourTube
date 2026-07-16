import re
from urllib.parse import urlparse

from pydantic import BaseModel, HttpUrl, field_validator
from datetime import datetime
from .base import BaseSchema
from .sync_run import LatestSyncSummary, SyncRunOut

# --- Input Schemas ---


class ChannelCreate(BaseModel):
    """
    Schema for adding a new channel. The user provides the handle
    and optionally which folder to place it in.
    """

    handle: str
    folder_id: str | None = None

    @field_validator("handle")
    @classmethod
    def validate_supported_handle(cls, value: str) -> str:
        candidate = value.strip()
        parsed = urlparse(candidate)
        if parsed.scheme or parsed.netloc:
            if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() not in {
                "youtube.com",
                "www.youtube.com",
                "m.youtube.com",
            }:
                raise ValueError("Use a YouTube channel URL containing an @handle.")
            segments = [segment for segment in parsed.path.split("/") if segment]
            candidate = segments[0] if segments else ""

        candidate = candidate.removeprefix("@")
        if not re.fullmatch(r"[\w.-]{3,30}", candidate, flags=re.UNICODE):
            raise ValueError("Use a YouTube @handle or a channel URL containing an @handle.")
        return value.strip()


class ChannelUpdate(BaseModel):
    """Schema for updating app-specific channel metadata."""

    is_favorited: bool | None = None
    folder_id: str | None = None  # Allows moving a channel
    tag_ids: list[str] | None = None  # List of tag IDs to associate with the channel


# --- Output Schema ---


class ChannelOut(BaseSchema):
    """Schema for returning a channel from the API."""

    id: str
    title: str
    handle: str | None
    description: str | None
    thumbnail_url: HttpUrl | None
    is_favorited: bool
    folder_id: str | None
    created_at: datetime
    last_updated: datetime

    # Calculated fields
    total_videos: int = 0
    latest_sync: LatestSyncSummary | None = None
    tag_ids: list[str] = []


class ChannelCreateResult(BaseModel):
    """A followed channel and the durable state of its first synchronization."""

    channel: ChannelOut
    initial_sync: SyncRunOut
