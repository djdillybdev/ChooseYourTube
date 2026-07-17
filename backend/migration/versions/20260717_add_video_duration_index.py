"""add video duration index

Revision ID: 20260717_video_duration
Revises: 20260716_category_icons
Create Date: 2026-07-17
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260717_video_duration"
down_revision: str | Sequence[str] | None = "20260716_category_icons"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_video_owner_duration",
        "videos",
        ["owner_id", "duration_seconds"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_video_owner_duration", table_name="videos")
