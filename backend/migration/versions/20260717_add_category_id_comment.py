"""add category id comment

Revision ID: 20260717_category_comment
Revises: 20260717_video_duration
Create Date: 2026-07-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260717_category_comment"
down_revision: str | Sequence[str] | None = "20260717_video_duration"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "categories",
        "id",
        existing_type=sa.String(length=36),
        existing_nullable=False,
        comment="UUID as string",
    )


def downgrade() -> None:
    op.alter_column(
        "categories",
        "id",
        existing_type=sa.String(length=36),
        existing_nullable=False,
        existing_comment="UUID as string",
        comment=None,
    )
