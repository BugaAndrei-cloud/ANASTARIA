"""strengthen marketplace item invariants

Revision ID: a31d8e42f907
Revises: f2c91b07a6de
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "a31d8e42f907"
down_revision: str | None = "f2c91b07a6de"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("uq_market_proceeds_numeric_asset", "marketplace_proceeds_components", ["proceeds_id", "payment_asset_id"], unique=True, postgresql_where=sa.text("openmu_item_id IS NULL"))
    op.create_table("marketplace_item_locations",
        sa.Column("openmu_item_id", sa.Uuid(), nullable=False),
        sa.Column("location_type", sa.Enum("ESCROW", "DELIVERY", "PROCEEDS", name="marketplaceitemlocationtype", native_enum=False), nullable=False),
        sa.Column("location_reference_id", sa.Uuid(), nullable=False),
        sa.Column("owner_account_id", sa.Uuid(), nullable=True),
        sa.Column("fencing_token", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("fencing_token > 0", name="ck_market_item_location_fence"),
        sa.PrimaryKeyConstraint("openmu_item_id"),
        sa.UniqueConstraint("location_type", "location_reference_id", "openmu_item_id", name="uq_market_item_location_reference"))
    op.create_index("ix_marketplace_item_locations_owner_account_id", "marketplace_item_locations", ["owner_account_id"])


def downgrade() -> None:
    op.drop_index("ix_marketplace_item_locations_owner_account_id", table_name="marketplace_item_locations")
    op.drop_table("marketplace_item_locations")
    op.drop_index("uq_market_proceeds_numeric_asset", table_name="marketplace_proceeds_components")
