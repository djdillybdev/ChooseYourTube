from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from .base import BaseSchema


def _trim_name(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("Category name must not be empty")
    return normalized


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return _trim_name(value)


class CategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)

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
    created_at: datetime
    channel_ids: list[str] = Field(default_factory=list)
