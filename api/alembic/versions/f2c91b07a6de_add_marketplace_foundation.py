"""add marketplace foundation

Revision ID: f2c91b07a6de
Revises: e4b9c1a73d20
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f2c91b07a6de"
down_revision: str | None = "e4b9c1a73d20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

listing_status = sa.Enum("PENDING_ESCROW", "ACTIVE", "PROCESSING", "SOLD", "CANCEL_PENDING", "CANCELLED", "EXPIRED", "FAILED", name="marketplacelistingstatus", native_enum=False)
asset_type = sa.Enum("NUMERIC_BALANCE", "PHYSICAL_ITEM", name="marketplaceassettype", native_enum=False)
command_type = sa.Enum("CREATE_LISTING", "BUY_LISTING", "CANCEL_LISTING", "CLAIM_DELIVERY", "CLAIM_PROCEEDS", name="marketplacecommandtype", native_enum=False)
command_status = sa.Enum("PENDING", "PROCESSING", "SUCCEEDED", "RETRYABLE_FAILED", "PERMANENT_FAILED", name="marketplacecommandstatus", native_enum=False)
transaction_status = sa.Enum("CREATED", "PROCESSING", "PAYMENT_RESERVED", "ITEM_TRANSFERRED", "COMPLETED", "ROLLBACK_REQUIRED", "FAILED", name="marketplacetransactionstatus", native_enum=False)
claim_status = sa.Enum("PENDING", "CLAIMING", "CLAIMED", "FAILED", name="marketplaceclaimstatus", native_enum=False)


def upgrade() -> None:
    op.create_table("marketplace_payment_assets",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("code", sa.String(64), nullable=False), sa.Column("asset_type", asset_type, nullable=False),
        sa.Column("openmu_item_definition_id", sa.Uuid(), nullable=True), sa.Column("enabled", sa.Boolean(), nullable=False), sa.Column("display_name_key", sa.String(160), nullable=False),
        sa.Column("icon_reference", sa.String(500), nullable=True), sa.Column("min_amount", sa.BigInteger(), nullable=False), sa.Column("max_amount", sa.BigInteger(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False), sa.Column("can_be_listing_price", sa.Boolean(), nullable=False), sa.Column("can_be_fee", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("min_amount > 0", name="ck_market_asset_min_positive"), sa.CheckConstraint("max_amount IS NULL OR max_amount >= min_amount", name="ck_market_asset_max_valid"),
        sa.CheckConstraint("asset_type = 'PHYSICAL_ITEM' OR openmu_item_definition_id IS NULL", name="ck_market_asset_definition_kind"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("code"))
    op.create_index("ix_market_assets_enabled_sort", "marketplace_payment_assets", ["enabled", "sort_order"])

    op.create_table("marketplace_listings",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("seller_account_id", sa.Uuid(), nullable=False), sa.Column("seller_character_id", sa.Uuid(), nullable=True),
        sa.Column("buyer_account_id", sa.Uuid(), nullable=True), sa.Column("openmu_item_id", sa.Uuid(), nullable=False), sa.Column("status", listing_status, nullable=False),
        sa.Column("item_snapshot_version", sa.Integer(), nullable=False), sa.Column("item_snapshot", sa.JSON(), nullable=False), sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sold_at", sa.DateTime(timezone=True), nullable=True), sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("item_snapshot_version > 0", name="ck_market_listing_snapshot_version"), sa.CheckConstraint("version > 0", name="ck_market_listing_version"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_market_listings_seller_account_id", "marketplace_listings", ["seller_account_id"])
    op.create_index("ix_market_listings_buyer_account_id", "marketplace_listings", ["buyer_account_id"])
    op.create_index("ix_market_listings_browse", "marketplace_listings", ["status", "created_at"])
    op.create_index("uq_market_listing_live_item", "marketplace_listings", ["openmu_item_id"], unique=True, postgresql_where=sa.text("status IN ('PENDING_ESCROW','ACTIVE','PROCESSING','CANCEL_PENDING')"))

    op.create_table("marketplace_listing_price_components",
        sa.Column("listing_id", sa.Uuid(), nullable=False), sa.Column("payment_asset_id", sa.Uuid(), nullable=False), sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_market_price_amount_positive"),
        sa.ForeignKeyConstraint(["listing_id"], ["marketplace_listings.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["payment_asset_id"], ["marketplace_payment_assets.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("listing_id", "payment_asset_id"))

    op.create_table("marketplace_commands",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("command_type", command_type, nullable=False), sa.Column("aggregate_type", sa.String(64), nullable=False), sa.Column("aggregate_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False), sa.Column("character_id", sa.Uuid(), nullable=True), sa.Column("idempotency_key", sa.String(128), nullable=False), sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False), sa.Column("status", command_status, nullable=False), sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("available_at", sa.DateTime(timezone=True), nullable=False), sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True), sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True), sa.Column("last_error_code", sa.String(96), nullable=True),
        sa.Column("correlation_id", sa.Uuid(), nullable=False), sa.Column("causation_id", sa.Uuid(), nullable=True), sa.CheckConstraint("attempts >= 0", name="ck_market_command_attempts"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("account_id", "command_type", "idempotency_key", name="uq_market_command_idempotency"))
    op.create_index("ix_market_commands_correlation_id", "marketplace_commands", ["correlation_id"])
    op.create_index("ix_market_commands_worker", "marketplace_commands", ["status", "available_at", "created_at"])

    op.create_table("marketplace_idempotency",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("account_id", sa.Uuid(), nullable=False), sa.Column("operation", sa.String(64), nullable=False), sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False), sa.Column("command_id", sa.Uuid(), nullable=True), sa.Column("response_status", sa.Integer(), nullable=True), sa.Column("response_body", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["command_id"], ["marketplace_commands.id"], ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_id", "operation", "idempotency_key", name="uq_market_idempotency_scope"))

    op.create_table("marketplace_transactions",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("listing_id", sa.Uuid(), nullable=False), sa.Column("seller_account_id", sa.Uuid(), nullable=False), sa.Column("buyer_account_id", sa.Uuid(), nullable=False),
        sa.Column("status", transaction_status, nullable=False), sa.Column("correlation_id", sa.Uuid(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True), sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True), sa.Column("failure_code", sa.String(96), nullable=True),
        sa.CheckConstraint("seller_account_id <> buyer_account_id", name="ck_market_transaction_distinct_accounts"), sa.ForeignKeyConstraint(["listing_id"], ["marketplace_listings.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("listing_id"), sa.UniqueConstraint("correlation_id"))

    op.create_table("marketplace_deliveries",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("owner_account_id", sa.Uuid(), nullable=False), sa.Column("openmu_item_id", sa.Uuid(), nullable=False), sa.Column("source_transaction_id", sa.Uuid(), nullable=False),
        sa.Column("status", claim_status, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["source_transaction_id"], ["marketplace_transactions.id"], ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_marketplace_deliveries_owner_account_id", "marketplace_deliveries", ["owner_account_id"])
    op.create_index("uq_market_delivery_live_item", "marketplace_deliveries", ["openmu_item_id"], unique=True, postgresql_where=sa.text("status IN ('PENDING','CLAIMING')"))

    op.create_table("marketplace_proceeds",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("owner_account_id", sa.Uuid(), nullable=False), sa.Column("source_transaction_id", sa.Uuid(), nullable=False), sa.Column("status", claim_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["source_transaction_id"], ["marketplace_transactions.id"], ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("source_transaction_id"))
    op.create_index("ix_marketplace_proceeds_owner_account_id", "marketplace_proceeds", ["owner_account_id"])

    op.create_table("marketplace_proceeds_components",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("proceeds_id", sa.Uuid(), nullable=False), sa.Column("payment_asset_id", sa.Uuid(), nullable=False), sa.Column("amount", sa.BigInteger(), nullable=False), sa.Column("openmu_item_id", sa.Uuid(), nullable=True),
        sa.CheckConstraint("amount > 0", name="ck_market_proceeds_amount_positive"), sa.ForeignKeyConstraint(["payment_asset_id"], ["marketplace_payment_assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proceeds_id"], ["marketplace_proceeds.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("proceeds_id", "payment_asset_id", "openmu_item_id", name="uq_market_proceeds_component"))
    op.create_index("uq_market_proceeds_physical_item", "marketplace_proceeds_components", ["openmu_item_id"], unique=True, postgresql_where=sa.text("openmu_item_id IS NOT NULL"))

    op.create_table("marketplace_audit_events",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("event_type", sa.String(64), nullable=False), sa.Column("correlation_id", sa.Uuid(), nullable=False), sa.Column("account_id", sa.Uuid(), nullable=True),
        sa.Column("listing_id", sa.Uuid(), nullable=True), sa.Column("transaction_id", sa.Uuid(), nullable=True), sa.Column("command_id", sa.Uuid(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False), sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["command_id"], ["marketplace_commands.id"], ondelete="SET NULL"), sa.ForeignKeyConstraint(["listing_id"], ["marketplace_listings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["transaction_id"], ["marketplace_transactions.id"], ondelete="SET NULL"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_marketplace_audit_events_account_id", "marketplace_audit_events", ["account_id"])
    op.create_index("ix_marketplace_audit_events_correlation_id", "marketplace_audit_events", ["correlation_id"])
    op.create_index("ix_market_audit_listing_time", "marketplace_audit_events", ["listing_id", "occurred_at"])

    op.create_table("marketplace_account_fences",
        sa.Column("account_id", sa.Uuid(), nullable=False), sa.Column("fencing_token", sa.BigInteger(), nullable=False), sa.Column("last_owner_id", sa.String(128), nullable=True), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("fencing_token >= 0", name="ck_market_fence_token"), sa.PrimaryKeyConstraint("account_id"))


def downgrade() -> None:
    op.drop_table("marketplace_account_fences")
    op.drop_index("ix_market_audit_listing_time", table_name="marketplace_audit_events")
    op.drop_index("ix_marketplace_audit_events_correlation_id", table_name="marketplace_audit_events")
    op.drop_index("ix_marketplace_audit_events_account_id", table_name="marketplace_audit_events")
    op.drop_table("marketplace_audit_events")
    op.drop_index("uq_market_proceeds_physical_item", table_name="marketplace_proceeds_components")
    op.drop_table("marketplace_proceeds_components")
    op.drop_index("ix_marketplace_proceeds_owner_account_id", table_name="marketplace_proceeds")
    op.drop_table("marketplace_proceeds")
    op.drop_index("uq_market_delivery_live_item", table_name="marketplace_deliveries")
    op.drop_index("ix_marketplace_deliveries_owner_account_id", table_name="marketplace_deliveries")
    op.drop_table("marketplace_deliveries")
    op.drop_table("marketplace_transactions")
    op.drop_table("marketplace_idempotency")
    op.drop_index("ix_market_commands_worker", table_name="marketplace_commands")
    op.drop_index("ix_market_commands_correlation_id", table_name="marketplace_commands")
    op.drop_table("marketplace_commands")
    op.drop_table("marketplace_listing_price_components")
    op.drop_index("uq_market_listing_live_item", table_name="marketplace_listings")
    op.drop_index("ix_market_listings_browse", table_name="marketplace_listings")
    op.drop_index("ix_market_listings_buyer_account_id", table_name="marketplace_listings")
    op.drop_index("ix_market_listings_seller_account_id", table_name="marketplace_listings")
    op.drop_table("marketplace_listings")
    op.drop_index("ix_market_assets_enabled_sort", table_name="marketplace_payment_assets")
    op.drop_table("marketplace_payment_assets")
