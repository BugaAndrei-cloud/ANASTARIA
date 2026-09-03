"""add events and site settings

Revision ID: 7a1c4d2e9f10
Revises: 28c17fef0ebb
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "7a1c4d2e9f10"
down_revision: Union[str, Sequence[str], None] = "28c17fef0ebb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "game_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("translations", sa.JSON(), nullable=False),
        sa.Column("schedule", sa.String(120), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("reward_summary", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_game_events_id", "game_events", ["id"])
    op.create_table(
        "site_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(100), nullable=False, unique=True),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_site_settings_id", "site_settings", ["id"])


def downgrade() -> None:
    op.drop_index("ix_site_settings_id", table_name="site_settings")
    op.drop_table("site_settings")
    op.drop_index("ix_game_events_id", table_name="game_events")
    op.drop_table("game_events")
