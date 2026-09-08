import unittest
import uuid

from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.base import Base
import app.models  # noqa: F401
from app.models.marketplace import MarketplaceAssetType, MarketplaceClaimStatus, MarketplaceCommand, MarketplaceCommandType, MarketplaceDelivery, MarketplaceItemLocation, MarketplaceItemLocationType, MarketplaceListing, MarketplaceListingPriceComponent, MarketplaceListingStatus, MarketplacePaymentAsset, MarketplaceTransaction, MarketplaceTransactionStatus
from app.schemas.marketplace import MarketplaceCompositePriceInput
from app.services.marketplace_domain import IdempotencyConflict, InvalidStateTransition, MarketplaceDomainError, create_idempotent_command, validate_listing_transition, validate_price_asset


class MarketplaceFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(cls.engine)

    def setUp(self):
        self.session = Session(self.engine)

    def tearDown(self):
        self.session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            self.session.execute(table.delete())
        self.session.commit()
        self.session.close()

    def listing(self, item_id, status=MarketplaceListingStatus.ACTIVE):
        return MarketplaceListing(seller_account_id=uuid.uuid4(), openmu_item_id=item_id, status=status, item_snapshot_version=1, item_snapshot={"schema_version": 1}, version=1)

    def test_duplicate_live_listing_for_item_is_rejected(self):
        item_id = uuid.uuid4()
        self.session.add(self.listing(item_id))
        self.session.commit()
        self.session.add(self.listing(item_id, MarketplaceListingStatus.PENDING_ESCROW))
        with self.assertRaises(IntegrityError):
            self.session.commit()

    def test_terminal_listing_does_not_block_new_listing(self):
        item_id = uuid.uuid4()
        self.session.add(self.listing(item_id, MarketplaceListingStatus.CANCELLED))
        self.session.add(self.listing(item_id, MarketplaceListingStatus.PENDING_ESCROW))
        self.session.commit()

    def test_duplicate_price_asset_and_non_positive_amount_are_rejected(self):
        asset = MarketplacePaymentAsset(code="TEST", asset_type=MarketplaceAssetType.NUMERIC_BALANCE, display_name_key="market.asset.test", min_amount=1)
        listing = self.listing(uuid.uuid4())
        self.session.add_all([asset, listing]); self.session.flush()
        self.session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=asset.id, amount=1)); self.session.commit()
        self.session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=asset.id, amount=2))
        with self.assertRaises(IntegrityError): self.session.commit()
        self.session.rollback()
        for code, amount in (("ZERO", 0), ("NEGATIVE", -1)):
            other = MarketplacePaymentAsset(code=code, asset_type=MarketplaceAssetType.NUMERIC_BALANCE, display_name_key=f"market.asset.{code.lower()}", min_amount=1)
            self.session.add(other); self.session.flush(); self.session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=other.id, amount=amount))
            with self.assertRaises(IntegrityError): self.session.commit()
            self.session.rollback()

    def test_schema_rejects_duplicate_assets(self):
        asset_id = uuid.uuid4()
        with self.assertRaises(ValidationError):
            MarketplaceCompositePriceInput(components=[{"payment_asset_id": asset_id, "amount": 1}, {"payment_asset_id": asset_id, "amount": 2}])

    def test_disabled_and_out_of_range_assets_are_rejected(self):
        asset = MarketplacePaymentAsset(code="DISABLED", asset_type=MarketplaceAssetType.NUMERIC_BALANCE, display_name_key="market.asset.disabled", enabled=False, min_amount=2, max_amount=3)
        with self.assertRaises(MarketplaceDomainError): validate_price_asset(asset, 2)
        asset.enabled = True
        with self.assertRaises(MarketplaceDomainError): validate_price_asset(asset, 1)
        with self.assertRaises(MarketplaceDomainError): validate_price_asset(asset, 4)

    def test_listing_state_machine(self):
        validate_listing_transition(MarketplaceListingStatus.ACTIVE, MarketplaceListingStatus.PROCESSING)
        with self.assertRaises(InvalidStateTransition):
            validate_listing_transition(MarketplaceListingStatus.SOLD, MarketplaceListingStatus.ACTIVE)

    def test_idempotent_command_reuses_same_payload_and_rejects_different_payload(self):
        account_id, aggregate_id, correlation_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        first, created = create_idempotent_command(self.session, account_id=account_id, operation=MarketplaceCommandType.BUY_LISTING, idempotency_key="retry-1", aggregate_type="listing", aggregate_id=aggregate_id, payload={"listing_id": str(aggregate_id)}, correlation_id=correlation_id)
        self.session.commit()
        same, created_again = create_idempotent_command(self.session, account_id=account_id, operation=MarketplaceCommandType.BUY_LISTING, idempotency_key="retry-1", aggregate_type="listing", aggregate_id=aggregate_id, payload={"listing_id": str(aggregate_id)}, correlation_id=correlation_id)
        self.assertFalse(created_again); self.assertEqual(first.id, same.id)
        with self.assertRaises(IdempotencyConflict):
            create_idempotent_command(self.session, account_id=account_id, operation=MarketplaceCommandType.BUY_LISTING, idempotency_key="retry-1", aggregate_type="listing", aggregate_id=aggregate_id, payload={"listing_id": str(uuid.uuid4())}, correlation_id=correlation_id)

    def test_outbox_and_domain_state_rollback_together(self):
        listing = self.listing(uuid.uuid4(), MarketplaceListingStatus.PENDING_ESCROW)
        self.session.add(listing); self.session.flush()
        create_idempotent_command(self.session, account_id=listing.seller_account_id, operation=MarketplaceCommandType.CREATE_LISTING, idempotency_key="create-1", aggregate_type="listing", aggregate_id=listing.id, payload={"listing_id": str(listing.id)}, correlation_id=uuid.uuid4())
        self.session.rollback()
        self.assertIsNone(self.session.get(MarketplaceListing, listing.id))
        self.assertIsNone(self.session.scalar(select(MarketplaceCommand)))

    def test_duplicate_active_delivery_is_rejected(self):
        listing = self.listing(uuid.uuid4(), MarketplaceListingStatus.SOLD)
        self.session.add(listing); self.session.flush()
        transaction = MarketplaceTransaction(listing_id=listing.id, seller_account_id=listing.seller_account_id, buyer_account_id=uuid.uuid4(), status=MarketplaceTransactionStatus.COMPLETED, correlation_id=uuid.uuid4())
        item_id = uuid.uuid4()
        self.session.add(transaction); self.session.flush()
        self.session.add(MarketplaceDelivery(owner_account_id=transaction.buyer_account_id, openmu_item_id=item_id, source_transaction_id=transaction.id, status=MarketplaceClaimStatus.PENDING)); self.session.commit()
        self.session.add(MarketplaceDelivery(owner_account_id=transaction.buyer_account_id, openmu_item_id=item_id, source_transaction_id=transaction.id, status=MarketplaceClaimStatus.CLAIMING))
        with self.assertRaises(IntegrityError): self.session.commit()

    def test_item_has_only_one_global_market_location(self):
        item_id = uuid.uuid4()
        self.session.add(MarketplaceItemLocation(openmu_item_id=item_id, location_type=MarketplaceItemLocationType.ESCROW, location_reference_id=uuid.uuid4(), fencing_token=1))
        self.session.commit()
        self.session.add(MarketplaceItemLocation(openmu_item_id=item_id, location_type=MarketplaceItemLocationType.DELIVERY, location_reference_id=uuid.uuid4(), owner_account_id=uuid.uuid4(), fencing_token=2))
        with self.assertRaises(IntegrityError): self.session.commit()


if __name__ == "__main__":
    unittest.main()
