"""add refresh sessions table

Revision ID: 20260305_refresh_sessions
Revises: 20260218_channel_playlist_src
Create Date: 2026-03-05 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260305_refresh_sessions"
down_revision: Union[str, Sequence[str], None] = "20260218_channel_playlist_src"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("replaced_by_id", sa.Uuid(), nullable=True),
        sa.Column("user_agent", sa.String(length=1024), nullable=True),
        sa.Column("ip_address", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["refresh_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["replaced_by_id"], ["refresh_sessions.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_refresh_sessions_expires_at"),
        "refresh_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_refresh_sessions_session_id"),
        "refresh_sessions",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_refresh_sessions_token_hash"),
        "refresh_sessions",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_refresh_sessions_user_id"),
        "refresh_sessions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_refresh_sessions_user_id"), table_name="refresh_sessions")
    op.drop_index(op.f("ix_refresh_sessions_token_hash"), table_name="refresh_sessions")
    op.drop_index(op.f("ix_refresh_sessions_session_id"), table_name="refresh_sessions")
    op.drop_index(op.f("ix_refresh_sessions_expires_at"), table_name="refresh_sessions")
    op.drop_table("refresh_sessions")
