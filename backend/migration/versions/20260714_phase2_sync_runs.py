"""add durable synchronization and quota state

Revision ID: 20260714_phase2_sync
Revises: 20260305_refresh_sessions
Create Date: 2026-07-14
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260714_phase2_sync"
down_revision: str | Sequence[str] | None = "20260305_refresh_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("channels", sa.Column("rss_etag", sa.String(512), nullable=True))
    op.add_column(
        "channels", sa.Column("rss_last_modified", sa.String(128), nullable=True)
    )

    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column(
            "status", sa.String(16), server_default="queued", nullable=False
        ),
        sa.Column("channel_id", sa.String(32), nullable=True),
        sa.Column("subscription_import_id", sa.Uuid(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="4", nullable=False),
        sa.Column("items_discovered", sa.Integer(), server_default="0", nullable=False),
        sa.Column("items_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("items_updated", sa.Integer(), server_default="0", nullable=False),
        sa.Column("items_skipped", sa.Integer(), server_default="0", nullable=False),
        sa.Column("items_failed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "kind IN ('initial_channel_sync', 'channel_refresh', 'playlist_sync', "
            "'subscription_import', 'demo_maintenance')",
            name="ck_sync_runs_kind",
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'partial', 'failed')",
            name="ck_sync_runs_status",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "channel_id"],
            ["channels.owner_id", "channels.id"],
            name="fk_sync_runs_channel",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_sync_runs_owner_queued", "sync_runs", ["owner_id", "queued_at"]
    )
    op.create_index("ix_sync_runs_status", "sync_runs", ["status"])
    op.create_index(
        "ix_sync_runs_channel", "sync_runs", ["owner_id", "channel_id"]
    )
    op.create_index(
        "ix_sync_runs_import",
        "sync_runs",
        ["owner_id", "subscription_import_id"],
    )
    op.create_index(
        "uq_sync_runs_active_channel_kind",
        "sync_runs",
        ["owner_id", "channel_id", "kind"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('queued', 'running') AND channel_id IS NOT NULL"
        ),
    )

    op.create_table(
        "youtube_api_usage",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("operation", sa.String(64), nullable=False),
        sa.Column("outcome", sa.String(24), nullable=False),
        sa.Column("estimated_units", sa.Integer(), server_default="0", nullable=False),
        sa.Column("call_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("estimated_units >= 0", name="ck_youtube_usage_units"),
        sa.CheckConstraint("call_count >= 0", name="ck_youtube_usage_calls"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "usage_date", "operation", "outcome", name="uq_youtube_usage_bucket"
        ),
    )
    op.create_index(
        "ix_youtube_usage_date", "youtube_api_usage", ["usage_date"]
    )


def downgrade() -> None:
    op.drop_index("ix_youtube_usage_date", table_name="youtube_api_usage")
    op.drop_table("youtube_api_usage")
    op.drop_index("uq_sync_runs_active_channel_kind", table_name="sync_runs")
    op.drop_index("ix_sync_runs_import", table_name="sync_runs")
    op.drop_index("ix_sync_runs_channel", table_name="sync_runs")
    op.drop_index("ix_sync_runs_status", table_name="sync_runs")
    op.drop_index("ix_sync_runs_owner_queued", table_name="sync_runs")
    op.drop_table("sync_runs")
    op.drop_column("channels", "rss_last_modified")
    op.drop_column("channels", "rss_etag")
