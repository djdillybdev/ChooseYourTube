"""add Watch Later system playlist identity

Revision ID: 20260714_phase3_org
Revises: 20260714_phase2_sync
Create Date: 2026-07-14
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260714_phase3_org"
down_revision: str | Sequence[str] | None = "20260714_phase2_sync"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("playlists", sa.Column("system_key", sa.String(32), nullable=True))
    op.create_index(
        "uq_playlist_owner_system_key",
        "playlists",
        ["owner_id", "system_key"],
        unique=True,
        postgresql_where=sa.text("system_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_playlist_owner_system_key", table_name="playlists")
    op.drop_column("playlists", "system_key")
