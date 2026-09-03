"""add account security questions

Revision ID: e4b9c1a73d20
Revises: d1a2948bc703
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e4b9c1a73d20"
down_revision: Union[str, Sequence[str], None] = "d1a2948bc703"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("password_reset_tokens", sa.Column("purpose", sa.String(20), server_default="email", nullable=False))
    op.add_column("password_reset_tokens", sa.Column("attempts", sa.Integer(), server_default="0", nullable=False))
    op.create_table(
        "account_security_questions",
        sa.Column("account_id", sa.String(36), primary_key=True),
        sa.Column("question", sa.String(160), nullable=False),
        sa.Column("answer_hash", sa.String(60), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("account_security_questions")
    op.drop_column("password_reset_tokens", "attempts")
    op.drop_column("password_reset_tokens", "purpose")
