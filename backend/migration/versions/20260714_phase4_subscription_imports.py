"""add subscription import workflow

Revision ID: 20260714_phase4_imports
Revises: 20260714_phase3_org
Create Date: 2026-07-14
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260714_phase4_imports"
down_revision: str | Sequence[str] | None = "20260714_phase3_org"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "subscription_imports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), server_default="collecting", nullable=False),
        sa.Column("candidate_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("new_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("existing_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("invalid_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("selected_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("imported_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("destination_folder_id", sa.String(36), nullable=True),
        sa.Column("destination_tag_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("oauth_state_hash", sa.String(64), nullable=True),
        sa.Column("oauth_state_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("oauth_state_consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ready_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "source IN ('youtube_oauth', 'youtube_takeout_csv')",
            name="ck_subscription_imports_source",
        ),
        sa.CheckConstraint(
            "status IN ('collecting', 'ready', 'queued', 'running', "
            "'succeeded', 'partial', 'failed')",
            name="ck_subscription_imports_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "id", name="uq_subscription_import_owner_id"),
    )
    op.create_index(
        "ix_subscription_imports_owner_created",
        "subscription_imports",
        ["owner_id", "created_at"],
    )
    op.create_index(
        "ix_subscription_imports_status", "subscription_imports", ["owner_id", "status"]
    )
    op.create_index(
        "ix_subscription_imports_oauth_state",
        "subscription_imports",
        ["oauth_state_hash"],
        unique=True,
        postgresql_where=sa.text("oauth_state_hash IS NOT NULL"),
    )

    op.create_table(
        "subscription_import_candidates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("import_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("channel_id", sa.String(32), nullable=True),
        sa.Column("channel_title", sa.String(255), nullable=True),
        sa.Column("channel_url", sa.String(512), nullable=True),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("source_index", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "state IN ('new', 'existing', 'invalid', 'selected', 'imported', 'failed')",
            name="ck_subscription_import_candidates_state",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id", "import_id"],
            ["subscription_imports.owner_id", "subscription_imports.id"],
            ondelete="CASCADE",
            name="fk_subscription_import_candidates_import",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("import_id", "source_index", name="uq_import_candidate_source_index"),
    )
    op.create_index(
        "ix_import_candidates_import_state",
        "subscription_import_candidates",
        ["owner_id", "import_id", "state"],
    )
    op.create_index(
        "uq_import_candidates_channel",
        "subscription_import_candidates",
        ["import_id", "channel_id"],
        unique=True,
        postgresql_where=sa.text("channel_id IS NOT NULL"),
    )

    op.create_foreign_key(
        "fk_sync_runs_subscription_import",
        "sync_runs",
        "subscription_imports",
        ["owner_id", "subscription_import_id"],
        ["owner_id", "id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "uq_sync_runs_active_import_kind",
        "sync_runs",
        ["owner_id", "subscription_import_id", "kind"],
        unique=True,
        postgresql_where=sa.text(
            "status IN ('queued', 'running') AND subscription_import_id IS NOT NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index("uq_sync_runs_active_import_kind", table_name="sync_runs")
    op.drop_constraint(
        "fk_sync_runs_subscription_import", "sync_runs", type_="foreignkey"
    )
    op.drop_index("uq_import_candidates_channel", table_name="subscription_import_candidates")
    op.drop_index(
        "ix_import_candidates_import_state", table_name="subscription_import_candidates"
    )
    op.drop_table("subscription_import_candidates")
    op.drop_index("ix_subscription_imports_oauth_state", table_name="subscription_imports")
    op.drop_index("ix_subscription_imports_status", table_name="subscription_imports")
    op.drop_index("ix_subscription_imports_owner_created", table_name="subscription_imports")
    op.drop_table("subscription_imports")
