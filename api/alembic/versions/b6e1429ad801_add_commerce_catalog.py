"""add commerce catalog

Revision ID: b6e1429ad801
Revises: 7a1c4d2e9f10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b6e1429ad801"
down_revision: Union[str, Sequence[str], None] = "7a1c4d2e9f10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("currency_definitions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("code", sa.String(32), nullable=False, unique=True), sa.Column("name", sa.String(80), nullable=False), sa.Column("kind", sa.String(24), nullable=False), sa.Column("icon", sa.String(255)), sa.Column("purchasable", sa.Boolean(), nullable=False), sa.Column("active", sa.Boolean(), nullable=False), sa.Column("sort_order", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_currency_definitions_id", "currency_definitions", ["id"])
    op.create_table("coin_packages", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("title", sa.String(120), nullable=False), sa.Column("description", sa.Text()), sa.Column("currency_code", sa.String(32), nullable=False), sa.Column("coin_amount", sa.Integer(), nullable=False), sa.Column("bonus_amount", sa.Integer(), nullable=False), sa.Column("price_minor", sa.Integer(), nullable=False), sa.Column("settlement_currency", sa.String(3), nullable=False), sa.Column("image_url", sa.String(500)), sa.Column("featured", sa.Boolean(), nullable=False), sa.Column("active", sa.Boolean(), nullable=False), sa.Column("sort_order", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_coin_packages_id", "coin_packages", ["id"])
    op.create_table("shop_products", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("title", sa.String(120), nullable=False), sa.Column("description", sa.Text()), sa.Column("category", sa.String(50), nullable=False), sa.Column("currency_code", sa.String(32), nullable=False), sa.Column("price_amount", sa.Integer(), nullable=False), sa.Column("delivery_code", sa.String(160)), sa.Column("image_url", sa.String(500)), sa.Column("featured", sa.Boolean(), nullable=False), sa.Column("active", sa.Boolean(), nullable=False), sa.Column("sort_order", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_shop_products_id", "shop_products", ["id"])


def downgrade() -> None:
    op.drop_index("ix_shop_products_id", table_name="shop_products"); op.drop_table("shop_products")
    op.drop_index("ix_coin_packages_id", table_name="coin_packages"); op.drop_table("coin_packages")
    op.drop_index("ix_currency_definitions_id", table_name="currency_definitions"); op.drop_table("currency_definitions")
