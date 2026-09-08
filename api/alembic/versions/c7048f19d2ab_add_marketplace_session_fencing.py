"""add marketplace persistent session fencing

Revision ID: c7048f19d2ab
Revises: a31d8e42f907
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "c7048f19d2ab"
down_revision: str | None = "a31d8e42f907"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("marketplace_commands", sa.Column("blocked_reason_code", sa.String(96), nullable=True))
    op.add_column("marketplace_commands", sa.Column("worker_id", sa.String(128), nullable=True))
    op.add_column("marketplace_commands", sa.Column("worker_lease_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "marketplace_account_sessions",
        sa.Column("account_id", sa.Uuid(), primary_key=True),
        sa.Column("session_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("session_kind", sa.Enum("ONLINE", "OFFLINE_HELPER", name="marketplacesessionkind", native_enum=False), nullable=False),
        sa.Column("game_server_instance_id", sa.String(128), nullable=False),
        sa.Column("fencing_token", sa.BigInteger(), nullable=False),
        sa.Column("state", sa.Enum("STARTING", "ACTIVE", "STOPPING", name="marketplacesessionstate", native_enum=False), nullable=False),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("fencing_token > 0", name="ck_market_session_fence_positive"),
    )
    op.create_index("ix_market_sessions_lease", "marketplace_account_sessions", ["lease_expires_at"])
    op.create_table(
        "marketplace_account_reconciliations",
        sa.Column("account_id", sa.Uuid(), primary_key=True),
        sa.Column("required_fencing_token", sa.BigInteger(), nullable=False),
        sa.Column("required_reason_code", sa.String(96), nullable=False),
        sa.Column("required_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reconciled_fencing_token", sa.BigInteger(), nullable=True),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reconciled_by", sa.String(128), nullable=True),
        sa.CheckConstraint("required_fencing_token > 0", name="ck_market_reconciliation_required_fence"),
        sa.CheckConstraint("reconciled_fencing_token IS NULL OR reconciled_fencing_token >= required_fencing_token", name="ck_market_reconciliation_completed_fence"),
    )


def downgrade() -> None:
    op.drop_table("marketplace_account_reconciliations")
    op.drop_index("ix_market_sessions_lease", table_name="marketplace_account_sessions")
    op.drop_table("marketplace_account_sessions")
    op.drop_column("marketplace_commands", "worker_lease_expires_at")
    op.drop_column("marketplace_commands", "worker_id")
    op.drop_column("marketplace_commands", "blocked_reason_code")
