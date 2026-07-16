from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from .base import BaseSchema

ICON_KEY_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


def _trim_name(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("Category name must not be empty")
    return normalized


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    icon_key: str | None = Field(
        default=None, min_length=1, max_length=64, pattern=ICON_KEY_PATTERN
    )

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return _trim_name(value)


class CategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    icon_key: str | None = Field(
        default=None, min_length=1, max_length=64, pattern=ICON_KEY_PATTERN
    )

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return _trim_name(value)


class CategoryChannelsUpdate(BaseModel):
    channel_ids: list[str] = Field(default_factory=list)


class ChannelCategoriesUpdate(BaseModel):
    category_ids: list[str] = Field(default_factory=list)


class ChannelCategoriesOut(BaseModel):
    channel_id: str
    category_ids: list[str]


class CategoryOut(BaseSchema):
    id: str
    name: str
    icon_key: str | None = None
    created_at: datetime
    channel_ids: list[str] = Field(default_factory=list)
