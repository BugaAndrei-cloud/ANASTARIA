"""link shop to OpenMU items

Revision ID: c8f7341ea920
Revises: b6e1429ad801
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c8f7341ea920"
down_revision: Union[str, Sequence[str], None] = "b6e1429ad801"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("shop_products", sa.Column("openmu_item_id", sa.String(36), nullable=True))
    op.add_column("shop_products", sa.Column("selected_options", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")))
    op.add_column("shop_products", sa.Column("discount_percent", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("shop_products", sa.Column("discount_starts_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("shop_products", sa.Column("discount_ends_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_shop_products_openmu_item_id", "shop_products", ["openmu_item_id"])


def downgrade() -> None:
    op.drop_index("ix_shop_products_openmu_item_id", table_name="shop_products")
    op.drop_column("shop_products", "discount_ends_at")
    op.drop_column("shop_products", "discount_starts_at")
    op.drop_column("shop_products", "discount_percent")
    op.drop_column("shop_products", "selected_options")
    op.drop_column("shop_products", "openmu_item_id")
