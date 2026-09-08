"""grant OpenMU least-privilege marketplace session access

Revision ID: f104b7d6a91c
Revises: e926c53df40a
"""
from collections.abc import Sequence

from alembic import op


revision: str = "f104b7d6a91c"
down_revision: str | None = "e926c53df40a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE "
        "ON TABLE public.marketplace_account_sessions TO account"
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE "
        "ON TABLE public.marketplace_account_fences TO account"
    )


def downgrade() -> None:
    op.execute(
        "REVOKE SELECT, INSERT, UPDATE "
        "ON TABLE public.marketplace_account_fences FROM account"
    )
    op.execute(
        "REVOKE SELECT, INSERT, UPDATE, DELETE "
        "ON TABLE public.marketplace_account_sessions FROM account"
    )
