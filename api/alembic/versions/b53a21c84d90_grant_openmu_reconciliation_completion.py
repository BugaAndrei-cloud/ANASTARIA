"""grant OpenMU least-privilege reconciliation completion access

Revision ID: b53a21c84d90
Revises: f104b7d6a91c
"""
from collections.abc import Sequence

from alembic import op


revision: str = "b53a21c84d90"
down_revision: str | None = "f104b7d6a91c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "GRANT SELECT (account_id, required_fencing_token, reconciled_fencing_token) "
        "ON TABLE public.marketplace_account_reconciliations TO account"
    )
    op.execute(
        "GRANT UPDATE (reconciled_fencing_token, reconciled_at, reconciled_by) "
        "ON TABLE public.marketplace_account_reconciliations TO account"
    )


def downgrade() -> None:
    op.execute(
        "REVOKE UPDATE (reconciled_fencing_token, reconciled_at, reconciled_by) "
        "ON TABLE public.marketplace_account_reconciliations FROM account"
    )
    op.execute(
        "REVOKE SELECT (account_id, required_fencing_token, reconciled_fencing_token) "
        "ON TABLE public.marketplace_account_reconciliations FROM account"
    )
