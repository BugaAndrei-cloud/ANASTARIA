import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MarketplaceAssetType(str, enum.Enum):
    NUMERIC_BALANCE = "NUMERIC_BALANCE"
    PHYSICAL_ITEM = "PHYSICAL_ITEM"


class MarketplaceBalanceScope(str, enum.Enum):
    ACCOUNT_VAULT = "ACCOUNT_VAULT"
    CHARACTER_INVENTORY = "CHARACTER_INVENTORY"


class MarketplaceListingStatus(str, enum.Enum):
    PENDING_ESCROW = "PENDING_ESCROW"
    ACTIVE = "ACTIVE"
    PROCESSING = "PROCESSING"
    SOLD = "SOLD"
    CANCEL_PENDING = "CANCEL_PENDING"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"


class MarketplaceCommandType(str, enum.Enum):
    CREATE_LISTING = "CREATE_LISTING"
    BUY_LISTING = "BUY_LISTING"
    CANCEL_LISTING = "CANCEL_LISTING"
    CLAIM_DELIVERY = "CLAIM_DELIVERY"
    CLAIM_PROCEEDS = "CLAIM_PROCEEDS"


class MarketplaceCommandStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    RETRYABLE_FAILED = "RETRYABLE_FAILED"
    PERMANENT_FAILED = "PERMANENT_FAILED"


class MarketplaceSessionKind(str, enum.Enum):
    ONLINE = "ONLINE"
    OFFLINE_HELPER = "OFFLINE_HELPER"


class MarketplaceSessionState(str, enum.Enum):
    STARTING = "STARTING"
    ACTIVE = "ACTIVE"
    STOPPING = "STOPPING"


class MarketplaceTransactionStatus(str, enum.Enum):
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    PAYMENT_RESERVED = "PAYMENT_RESERVED"
    ITEM_TRANSFERRED = "ITEM_TRANSFERRED"
    COMPLETED = "COMPLETED"
    ROLLBACK_REQUIRED = "ROLLBACK_REQUIRED"
    FAILED = "FAILED"


class MarketplaceClaimStatus(str, enum.Enum):
    PENDING = "PENDING"
    CLAIMING = "CLAIMING"
    CLAIMED = "CLAIMED"
    FAILED = "FAILED"


class MarketplaceItemLocationType(str, enum.Enum):
    ESCROW = "ESCROW"
    DELIVERY = "DELIVERY"
    PROCEEDS = "PROCEEDS"


class MarketplacePaymentAsset(Base):
    __tablename__ = "marketplace_payment_assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    asset_type: Mapped[MarketplaceAssetType] = mapped_column(Enum(MarketplaceAssetType, native_enum=False, length=32), nullable=False)
    balance_scope: Mapped[MarketplaceBalanceScope | None] = mapped_column(Enum(MarketplaceBalanceScope, native_enum=False, length=32), nullable=True)
    openmu_item_definition_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    display_name_key: Mapped[str] = mapped_column(String(160), nullable=False)
    icon_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    min_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    max_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    can_be_listing_price: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    can_be_fee: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        CheckConstraint("min_amount > 0", name="ck_market_asset_min_positive"),
        CheckConstraint("max_amount IS NULL OR max_amount >= min_amount", name="ck_market_asset_max_valid"),
        CheckConstraint("asset_type = 'PHYSICAL_ITEM' OR openmu_item_definition_id IS NULL", name="ck_market_asset_definition_kind"),
        CheckConstraint("asset_type = 'NUMERIC_BALANCE' OR balance_scope IS NULL", name="ck_market_asset_balance_scope_kind"),
        Index("ix_market_assets_enabled_sort", "enabled", "sort_order"),
    )


class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    seller_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    seller_character_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    buyer_account_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    openmu_item_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[MarketplaceListingStatus] = mapped_column(Enum(MarketplaceListingStatus, native_enum=False, length=32), nullable=False)
    item_snapshot_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    item_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    price_components: Mapped[list["MarketplaceListingPriceComponent"]] = relationship(back_populates="listing", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("item_snapshot_version > 0", name="ck_market_listing_snapshot_version"),
        CheckConstraint("version > 0", name="ck_market_listing_version"),
        Index("ix_market_listings_browse", "status", "created_at"),
        Index("uq_market_listing_live_item", "openmu_item_id", unique=True, postgresql_where=text("status IN ('PENDING_ESCROW','ACTIVE','PROCESSING','CANCEL_PENDING')"), sqlite_where=text("status IN ('PENDING_ESCROW','ACTIVE','PROCESSING','CANCEL_PENDING')")),
    )


class MarketplaceListingPriceComponent(Base):
    __tablename__ = "marketplace_listing_price_components"

    listing_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("marketplace_listings.id", ondelete="CASCADE"), primary_key=True)
    payment_asset_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("marketplace_payment_assets.id", ondelete="RESTRICT"), primary_key=True)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    listing: Mapped[MarketplaceListing] = relationship(back_populates="price_components")

    __table_args__ = (CheckConstraint("amount > 0", name="ck_market_price_amount_positive"),)


class MarketplaceIdempotencyRecord(Base):
    __tablename__ = "marketplace_idempotency"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    command_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("marketplace_commands.id", ondelete="RESTRICT"), nullable=True)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("account_id", "operation", "idempotency_key", name="uq_market_idempotency_scope"),)


class MarketplaceCommand(Base):
    __tablename__ = "marketplace_commands"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    command_type: Mapped[MarketplaceCommandType] = mapped_column(Enum(MarketplaceCommandType, native_enum=False, length=32), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    character_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[MarketplaceCommandStatus] = mapped_column(Enum(MarketplaceCommandStatus, native_enum=False, length=32), nullable=False, default=MarketplaceCommandStatus.PENDING)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    blocked_reason_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    worker_lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    causation_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    __table_args__ = (
        UniqueConstraint("account_id", "command_type", "idempotency_key", name="uq_market_command_idempotency"),
        CheckConstraint("attempts >= 0", name="ck_market_command_attempts"),
        Index("ix_market_commands_worker", "status", "available_at", "created_at"),
    )


class MarketplaceTransaction(Base):
    __tablename__ = "marketplace_transactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("marketplace_listings.id", ondelete="RESTRICT"), nullable=False, unique=True)
    seller_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    buyer_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[MarketplaceTransactionStatus] = mapped_column(Enum(MarketplaceTransactionStatus, native_enum=False, length=32), nullable=False)
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(96), nullable=True)

    __table_args__ = (CheckConstraint("seller_account_id <> buyer_account_id", name="ck_market_transaction_distinct_accounts"),)


class MarketplaceDelivery(Base):
    __tablename__ = "marketplace_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    openmu_item_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    source_transaction_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("marketplace_transactions.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[MarketplaceClaimStatus] = mapped_column(Enum(MarketplaceClaimStatus, native_enum=False, length=24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("uq_market_delivery_live_item", "openmu_item_id", unique=True, postgresql_where=text("status IN ('PENDING','CLAIMING')"), sqlite_where=text("status IN ('PENDING','CLAIMING')")),)


class MarketplaceProceeds(Base):
    __tablename__ = "marketplace_proceeds"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_account_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    source_transaction_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("marketplace_transactions.id", ondelete="RESTRICT"), nullable=False, unique=True)
    status: Mapped[MarketplaceClaimStatus] = mapped_column(Enum(MarketplaceClaimStatus, native_enum=False, length=24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    components: Mapped[list["MarketplaceProceedsComponent"]] = relationship(back_populates="proceeds", cascade="all, delete-orphan")


class MarketplaceProceedsComponent(Base):
    __tablename__ = "marketplace_proceeds_components"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    proceeds_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("marketplace_proceeds.id", ondelete="CASCADE"), nullable=False)
    payment_asset_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("marketplace_payment_assets.id", ondelete="RESTRICT"), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    openmu_item_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    proceeds: Mapped[MarketplaceProceeds] = relationship(back_populates="components")

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_market_proceeds_amount_positive"),
        UniqueConstraint("proceeds_id", "payment_asset_id", "openmu_item_id", name="uq_market_proceeds_component"),
        Index("uq_market_proceeds_numeric_asset", "proceeds_id", "payment_asset_id", unique=True, postgresql_where=text("openmu_item_id IS NULL"), sqlite_where=text("openmu_item_id IS NULL")),
        Index("uq_market_proceeds_physical_item", "openmu_item_id", unique=True, postgresql_where=text("openmu_item_id IS NOT NULL"), sqlite_where=text("openmu_item_id IS NOT NULL")),
    )


class MarketplaceItemLocation(Base):
    """Global registry which prevents a physical UUID occupying two market locations."""

    __tablename__ = "marketplace_item_locations"

    openmu_item_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    location_type: Mapped[MarketplaceItemLocationType] = mapped_column(Enum(MarketplaceItemLocationType, native_enum=False, length=24), nullable=False)
    location_reference_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    owner_account_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    fencing_token: Mapped[int] = mapped_column(BigInteger, nullable=False)
    origin_storage_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    origin_item_slot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        CheckConstraint("fencing_token > 0", name="ck_market_item_location_fence"),
        UniqueConstraint("location_type", "location_reference_id", "openmu_item_id", name="uq_market_item_location_reference"),
    )


class MarketplacePhysicalStorage(Base):
    __tablename__ = "marketplace_physical_storages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    location_type: Mapped[MarketplaceItemLocationType] = mapped_column(Enum(MarketplaceItemLocationType, native_enum=False, length=24), nullable=False)
    location_reference_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    owner_account_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    openmu_item_storage_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (UniqueConstraint("location_type", "location_reference_id", name="uq_market_physical_storage_location"),)


class MarketplaceAuditEvent(Base):
    __tablename__ = "marketplace_audit_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    account_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    listing_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("marketplace_listings.id", ondelete="SET NULL"), nullable=True)
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("marketplace_transactions.id", ondelete="SET NULL"), nullable=True)
    command_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("marketplace_commands.id", ondelete="SET NULL"), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (Index("ix_market_audit_listing_time", "listing_id", "occurred_at"),)


class MarketplaceAccountFence(Base):
    __tablename__ = "marketplace_account_fences"

    account_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    fencing_token: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    last_owner_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (CheckConstraint("fencing_token >= 0", name="ck_market_fence_token"),)


class MarketplaceAccountSession(Base):
    __tablename__ = "marketplace_account_sessions"

    account_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, unique=True)
    session_kind: Mapped[MarketplaceSessionKind] = mapped_column(Enum(MarketplaceSessionKind, native_enum=False, length=24), nullable=False)
    game_server_instance_id: Mapped[str] = mapped_column(String(128), nullable=False)
    fencing_token: Mapped[int] = mapped_column(BigInteger, nullable=False)
    state: Mapped[MarketplaceSessionState] = mapped_column(Enum(MarketplaceSessionState, native_enum=False, length=16), nullable=False)
    heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lease_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        CheckConstraint("fencing_token > 0", name="ck_market_session_fence_positive"),
        Index("ix_market_sessions_lease", "lease_expires_at"),
    )


class MarketplaceAccountReconciliation(Base):
    __tablename__ = "marketplace_account_reconciliations"

    account_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    required_fencing_token: Mapped[int] = mapped_column(BigInteger, nullable=False)
    required_reason_code: Mapped[str] = mapped_column(String(96), nullable=False)
    required_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    reconciled_fencing_token: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reconciled_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        CheckConstraint("required_fencing_token > 0", name="ck_market_reconciliation_required_fence"),
        CheckConstraint("reconciled_fencing_token IS NULL OR reconciled_fencing_token >= required_fencing_token", name="ck_market_reconciliation_completed_fence"),
    )
