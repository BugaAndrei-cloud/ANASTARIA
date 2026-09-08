"""add marketplace physical storage semantics

Revision ID: d815a42be3fc
Revises: c7048f19d2ab
"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "d815a42be3fc"
down_revision: str | None = "c7048f19d2ab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("marketplace_payment_assets", sa.Column("balance_scope", sa.Enum("ACCOUNT_VAULT", "CHARACTER_INVENTORY", name="marketplacebalancescope", native_enum=False), nullable=True))
    op.execute("UPDATE marketplace_payment_assets SET balance_scope = 'ACCOUNT_VAULT' WHERE asset_type = 'NUMERIC_BALANCE'")
    op.create_check_constraint("ck_market_asset_balance_scope_kind", "marketplace_payment_assets", "asset_type = 'NUMERIC_BALANCE' OR balance_scope IS NULL")
    op.add_column("marketplace_item_locations", sa.Column("origin_storage_id", sa.Uuid(), nullable=True))
    op.add_column("marketplace_item_locations", sa.Column("origin_item_slot", sa.Integer(), nullable=True))
    op.create_table(
        "marketplace_physical_storages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("location_type", sa.Enum("ESCROW", "DELIVERY", "PROCEEDS", name="marketplaceitemlocationtype", native_enum=False), nullable=False),
        sa.Column("location_reference_id", sa.Uuid(), nullable=False),
        sa.Column("owner_account_id", sa.Uuid(), nullable=True),
        sa.Column("openmu_item_storage_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["openmu_item_storage_id"], ["data.ItemStorage.Id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("location_type", "location_reference_id", name="uq_market_physical_storage_location"),
    )


def downgrade() -> None:
    op.drop_table("marketplace_physical_storages")
    op.drop_column("marketplace_item_locations", "origin_item_slot")
    op.drop_column("marketplace_item_locations", "origin_storage_id")
    op.drop_constraint("ck_market_asset_balance_scope_kind", "marketplace_payment_assets", type_="check")
    op.drop_column("marketplace_payment_assets", "balance_scope")
