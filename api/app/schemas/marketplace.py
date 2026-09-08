import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.marketplace import MarketplaceAssetType, MarketplaceClaimStatus, MarketplaceCommandStatus, MarketplaceCommandType, MarketplaceItemLocationType, MarketplaceListingStatus, MarketplaceTransactionStatus


class MarketplacePaymentAssetSchema(BaseModel):
    id: uuid.UUID
    code: str
    asset_type: MarketplaceAssetType
    openmu_item_definition_id: uuid.UUID | None
    enabled: bool
    display_name_key: str
    icon_reference: str | None
    min_amount: int
    max_amount: int | None
    sort_order: int
    can_be_listing_price: bool
    can_be_fee: bool

    model_config = {"from_attributes": True}


class MarketplacePriceComponentInput(BaseModel):
    payment_asset_id: uuid.UUID
    amount: int = Field(gt=0)


class MarketplaceCompositePriceInput(BaseModel):
    components: list[MarketplacePriceComponentInput] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def unique_assets(self):
        ids = [component.payment_asset_id for component in self.components]
        if len(ids) != len(set(ids)):
            raise ValueError("MARKETPLACE_DUPLICATE_PAYMENT_ASSET")
        return self


class MarketplaceCreateListingInput(BaseModel):
    openmu_item_id: uuid.UUID
    character_id: uuid.UUID | None = None
    price: MarketplaceCompositePriceInput
    idempotency_key: str = Field(min_length=1, max_length=128)


class MarketplaceCreateListingResponse(BaseModel):
    listing: "MarketplaceListingSchema"
    command: "MarketplaceCommandSchema"
    created: bool


class MarketplaceBuyListingInput(BaseModel):
    character_id: uuid.UUID | None = None
    idempotency_key: str = Field(min_length=1, max_length=128)


class MarketplaceClaimInput(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=128)


class MarketplaceCommandSubmissionResponse(BaseModel):
    command: "MarketplaceCommandSchema"
    created: bool


class MarketplaceListingSchema(BaseModel):
    id: uuid.UUID
    seller_account_id: uuid.UUID
    seller_character_id: uuid.UUID | None
    buyer_account_id: uuid.UUID | None
    openmu_item_id: uuid.UUID
    status: MarketplaceListingStatus
    item_snapshot_version: int
    item_snapshot: dict
    version: int
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None
    sold_at: datetime | None
    cancelled_at: datetime | None

    model_config = {"from_attributes": True}


class MarketplaceCommandSchema(BaseModel):
    id: uuid.UUID
    command_type: MarketplaceCommandType
    aggregate_type: str
    aggregate_id: uuid.UUID
    status: MarketplaceCommandStatus
    attempts: int
    correlation_id: uuid.UUID
    created_at: datetime
    available_at: datetime
    completed_at: datetime | None
    last_error_code: str | None

    model_config = {"from_attributes": True}


class MarketplaceTransactionSchema(BaseModel):
    id: uuid.UUID
    listing_id: uuid.UUID
    seller_account_id: uuid.UUID
    buyer_account_id: uuid.UUID
    status: MarketplaceTransactionStatus
    correlation_id: uuid.UUID
    created_at: datetime
    completed_at: datetime | None
    failure_code: str | None

    model_config = {"from_attributes": True}


class MarketplaceClaimSchema(BaseModel):
    id: uuid.UUID
    owner_account_id: uuid.UUID
    status: MarketplaceClaimStatus
    created_at: datetime
    claimed_at: datetime | None

    model_config = {"from_attributes": True}
