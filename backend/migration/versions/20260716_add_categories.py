"""add channel categories

Revision ID: 20260716_categories
Revises: 20260714_phase4_imports
Create Date: 2026-07-16
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260716_categories"
down_revision: str | Sequence[str] | None = "20260714_phase4_imports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("normalized_name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "id", name="uq_category_owner_id"),
        sa.UniqueConstraint(
            "owner_id", "normalized_name", name="uq_category_owner_normalized_name"
        ),
    )
    op.create_index("ix_categories_id", "categories", ["id"])
    op.create_index("ix_categories_owner_id", "categories", ["owner_id"])

    op.create_table(
        "channel_categories",
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("channel_id", sa.String(32), nullable=False),
        sa.Column("category_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id", "channel_id"],
            ["channels.owner_id", "channels.id"],
            ondelete="CASCADE",
            name="fk_channel_categories_channel",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "category_id"],
            ["categories.owner_id", "categories.id"],
            ondelete="CASCADE",
            name="fk_channel_categories_category",
        ),
        sa.PrimaryKeyConstraint("owner_id", "channel_id", "category_id"),
    )


def downgrade() -> None:
    op.drop_table("channel_categories")
    op.drop_index("ix_categories_owner_id", table_name="categories")
    op.drop_index("ix_categories_id", table_name="categories")
    op.drop_table("categories")
