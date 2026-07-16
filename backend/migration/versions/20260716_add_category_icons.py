"""add category icon key

Revision ID: 20260716_category_icons
Revises: 20260716_categories
Create Date: 2026-07-16
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260716_category_icons"
down_revision: str | Sequence[str] | None = "20260716_categories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "categories", sa.Column("icon_key", sa.String(length=64), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("categories", "icon_key")
