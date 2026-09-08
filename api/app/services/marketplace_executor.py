"""Offline-only physical Marketplace command executor.

The caller owns one PostgreSQL transaction for the complete OpenMU and Marketplace mutation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.marketplace import (
    MarketplaceAssetType,
    MarketplaceAuditEvent,
    MarketplaceBalanceScope,
    MarketplaceClaimStatus,
    MarketplaceCommand,
    MarketplaceCommandStatus,
    MarketplaceCommandType,
    MarketplaceDelivery,
    MarketplaceIdempotencyRecord,
    MarketplaceItemLocation,
    MarketplaceItemLocationType,
    MarketplaceListing,
    MarketplaceListingStatus,
    MarketplacePaymentAsset,
    MarketplacePhysicalStorage,
    MarketplaceProceeds,
    MarketplaceProceedsComponent,
    MarketplaceTransaction,
    MarketplaceTransactionStatus,
)
from app.services.marketplace_domain import AccountNotSafe, claim_next_command, defer_unsafe_command, require_account_safe_for_mutation, validate_price_asset


class PhysicalExecutionError(RuntimeError):
    def __init__(self, code: str, *, retryable: bool = False):
        super().__init__(code)
        self.code = code
        self.retryable = retryable


class MarketplacePhysicalExecutor:
    """Executes a previously claimed command inside the caller's open transaction."""

    def execute(self, session: Session, command_id: uuid.UUID, worker_id: str) -> None:
        command = session.scalar(select(MarketplaceCommand).where(MarketplaceCommand.id == command_id).with_for_update())
        if command is None:
            raise PhysicalExecutionError("MARKETPLACE_COMMAND_NOT_FOUND")
        if command.status == MarketplaceCommandStatus.SUCCEEDED:
            return
        if command.status != MarketplaceCommandStatus.PROCESSING or command.worker_id != worker_id:
            raise PhysicalExecutionError("MARKETPLACE_COMMAND_NOT_OWNED")

        try:
            fence = require_account_safe_for_mutation(session, command.account_id)
            handlers = {
                MarketplaceCommandType.CREATE_LISTING: self._create,
                MarketplaceCommandType.BUY_LISTING: self._buy,
                MarketplaceCommandType.CANCEL_LISTING: self._cancel,
                MarketplaceCommandType.CLAIM_DELIVERY: self._claim_delivery,
                MarketplaceCommandType.CLAIM_PROCEEDS: self._claim_proceeds,
            }
            try:
                with session.begin_nested():
                    handlers[command.command_type](session, command, fence)
                    self._succeed(session, command)
            except PhysicalExecutionError as error:
                if error.retryable:
                    defer_unsafe_command(session, command, error.code)
                    return
                raise
        except AccountNotSafe as error:
            defer_unsafe_command(session, command, error.reason_code)

    def _create(self, session: Session, command: MarketplaceCommand, fence: int) -> None:
        listing = self._locked_listing(session, command.aggregate_id)
        if listing.status != MarketplaceListingStatus.PENDING_ESCROW or listing.seller_account_id != command.account_id:
            raise PhysicalExecutionError("MARKETPLACE_CREATE_INVALID_LISTING_STATE")
        self._validate_prices(listing)
        item = session.execute(text('SELECT "ItemStorageId", "ItemSlot" FROM data."Item" WHERE "Id"=:item FOR UPDATE'), {"item": listing.openmu_item_id}).one_or_none()
        if item is None:
            raise PhysicalExecutionError("MARKETPLACE_ITEM_NOT_FOUND")
        if not self._account_owns_storage(session, command.account_id, item.ItemStorageId):
            raise PhysicalExecutionError("MARKETPLACE_ITEM_NOT_OWNED")
        if session.get(MarketplaceItemLocation, listing.openmu_item_id) is not None:
            raise PhysicalExecutionError("MARKETPLACE_ITEM_ALREADY_MANAGED")
        storage_id = self._market_storage(session, MarketplaceItemLocationType.ESCROW, listing.id, command.account_id)
        self._move_item(session, listing.openmu_item_id, storage_id, 0)
        session.add(MarketplaceItemLocation(openmu_item_id=listing.openmu_item_id, location_type=MarketplaceItemLocationType.ESCROW, location_reference_id=listing.id, owner_account_id=command.account_id, fencing_token=fence, origin_storage_id=item.ItemStorageId, origin_item_slot=item.ItemSlot))
        listing.status = MarketplaceListingStatus.ACTIVE

    def _buy(self, session: Session, command: MarketplaceCommand, fence: int) -> None:
        listing = self._locked_listing(session, command.aggregate_id)
        if listing.status != MarketplaceListingStatus.ACTIVE:
            raise PhysicalExecutionError("MARKETPLACE_LISTING_NOT_ACTIVE")
        if listing.seller_account_id == command.account_id:
            raise PhysicalExecutionError("MARKETPLACE_BUYER_IS_SELLER")
        listing.status = MarketplaceListingStatus.PROCESSING
        transaction = MarketplaceTransaction(listing_id=listing.id, seller_account_id=listing.seller_account_id, buyer_account_id=command.account_id, status=MarketplaceTransactionStatus.PROCESSING, correlation_id=command.correlation_id, started_at=datetime.now(timezone.utc))
        session.add(transaction); session.flush()
        proceeds = MarketplaceProceeds(owner_account_id=listing.seller_account_id, source_transaction_id=transaction.id, status=MarketplaceClaimStatus.PENDING)
        session.add(proceeds); session.flush()

        for price in listing.price_components:
            asset = session.get(MarketplacePaymentAsset, price.payment_asset_id)
            if asset is None:
                raise PhysicalExecutionError("MARKETPLACE_ASSET_NOT_FOUND")
            validate_price_asset(asset, price.amount)
            if asset.asset_type == MarketplaceAssetType.NUMERIC_BALANCE:
                storage_id = self._balance_storage(session, command.account_id, command.character_id, asset)
                changed = session.execute(text('UPDATE data."ItemStorage" SET "Money"="Money"-:amount WHERE "Id"=:storage AND "Money">=:amount'), {"amount": price.amount, "storage": storage_id}).rowcount
                if changed != 1:
                    raise PhysicalExecutionError("MARKETPLACE_INSUFFICIENT_NUMERIC_BALANCE")
                session.add(MarketplaceProceedsComponent(proceeds_id=proceeds.id, payment_asset_id=asset.id, amount=price.amount))
            else:
                if asset.openmu_item_definition_id is None:
                    raise PhysicalExecutionError("MARKETPLACE_PHYSICAL_ASSET_DEFINITION_MISSING")
                vault_id, _ = self._vault(session, command.account_id)
                rows = session.execute(text('''SELECT i."Id" FROM data."Item" i
                    WHERE i."ItemStorageId"=:storage AND i."DefinitionId"=:definition
                      AND NOT EXISTS (SELECT 1 FROM marketplace_item_locations l WHERE l.openmu_item_id=i."Id")
                    ORDER BY i."Id" FOR UPDATE LIMIT :amount'''), {"storage": vault_id, "definition": asset.openmu_item_definition_id, "amount": price.amount}).all()
                if len(rows) != price.amount:
                    raise PhysicalExecutionError("MARKETPLACE_INSUFFICIENT_PHYSICAL_BALANCE")
                proceeds_storage = self._market_storage(session, MarketplaceItemLocationType.PROCEEDS, proceeds.id, listing.seller_account_id)
                for slot, row in enumerate(rows):
                    self._move_item(session, row.Id, proceeds_storage, slot)
                    session.add(MarketplaceProceedsComponent(proceeds_id=proceeds.id, payment_asset_id=asset.id, amount=1, openmu_item_id=row.Id))
                    session.add(MarketplaceItemLocation(openmu_item_id=row.Id, location_type=MarketplaceItemLocationType.PROCEEDS, location_reference_id=proceeds.id, owner_account_id=listing.seller_account_id, fencing_token=fence, origin_storage_id=vault_id))

        location = session.scalar(select(MarketplaceItemLocation).where(MarketplaceItemLocation.openmu_item_id == listing.openmu_item_id).with_for_update())
        if location is None or location.location_type != MarketplaceItemLocationType.ESCROW or location.location_reference_id != listing.id:
            raise PhysicalExecutionError("MARKETPLACE_ESCROW_INVARIANT_FAILED")
        delivery = MarketplaceDelivery(owner_account_id=command.account_id, openmu_item_id=listing.openmu_item_id, source_transaction_id=transaction.id, status=MarketplaceClaimStatus.PENDING)
        session.add(delivery); session.flush()
        delivery_storage = self._market_storage(session, MarketplaceItemLocationType.DELIVERY, delivery.id, command.account_id)
        self._move_item(session, listing.openmu_item_id, delivery_storage, 0)
        location.location_type = MarketplaceItemLocationType.DELIVERY
        location.location_reference_id = delivery.id
        location.owner_account_id = command.account_id
        location.fencing_token = fence
        listing.status = MarketplaceListingStatus.SOLD
        listing.buyer_account_id = command.account_id
        listing.sold_at = datetime.now(timezone.utc)
        transaction.status = MarketplaceTransactionStatus.COMPLETED
        transaction.completed_at = datetime.now(timezone.utc)

    def _cancel(self, session: Session, command: MarketplaceCommand, fence: int) -> None:
        listing = self._locked_listing(session, command.aggregate_id)
        if listing.seller_account_id != command.account_id or listing.status != MarketplaceListingStatus.ACTIVE:
            raise PhysicalExecutionError("MARKETPLACE_CANCEL_INVALID_STATE")
        location = session.scalar(select(MarketplaceItemLocation).where(MarketplaceItemLocation.openmu_item_id == listing.openmu_item_id).with_for_update())
        slot = self._find_vault_slots(session, command.account_id, [listing.openmu_item_id])
        if location is None or location.location_type != MarketplaceItemLocationType.ESCROW:
            raise PhysicalExecutionError("MARKETPLACE_ESCROW_INVARIANT_FAILED")
        if slot is None:
            raise PhysicalExecutionError("MARKETPLACE_VAULT_CAPACITY", retryable=True)
        vault_id, _ = self._vault(session, command.account_id)
        self._move_item(session, listing.openmu_item_id, vault_id, slot[listing.openmu_item_id])
        session.delete(location)
        listing.status = MarketplaceListingStatus.CANCELLED
        listing.cancelled_at = datetime.now(timezone.utc)

    def _claim_delivery(self, session: Session, command: MarketplaceCommand, fence: int) -> None:
        delivery = session.scalar(select(MarketplaceDelivery).where(MarketplaceDelivery.id == command.aggregate_id).with_for_update())
        if delivery is None or delivery.owner_account_id != command.account_id:
            raise PhysicalExecutionError("MARKETPLACE_DELIVERY_NOT_FOUND")
        if delivery.status == MarketplaceClaimStatus.CLAIMED:
            return
        slots = self._find_vault_slots(session, command.account_id, [delivery.openmu_item_id])
        if slots is None:
            raise PhysicalExecutionError("MARKETPLACE_VAULT_CAPACITY", retryable=True)
        vault_id, _ = self._vault(session, command.account_id)
        self._move_item(session, delivery.openmu_item_id, vault_id, slots[delivery.openmu_item_id])
        location = session.get(MarketplaceItemLocation, delivery.openmu_item_id)
        if location is None or location.location_type != MarketplaceItemLocationType.DELIVERY:
            raise PhysicalExecutionError("MARKETPLACE_DELIVERY_INVARIANT_FAILED")
        session.delete(location)
        delivery.status = MarketplaceClaimStatus.CLAIMED
        delivery.claimed_at = datetime.now(timezone.utc)

    def _claim_proceeds(self, session: Session, command: MarketplaceCommand, fence: int) -> None:
        proceeds = session.scalar(select(MarketplaceProceeds).where(MarketplaceProceeds.id == command.aggregate_id).with_for_update())
        if proceeds is None or proceeds.owner_account_id != command.account_id:
            raise PhysicalExecutionError("MARKETPLACE_PROCEEDS_NOT_FOUND")
        if proceeds.status == MarketplaceClaimStatus.CLAIMED:
            return
        physical_ids = [c.openmu_item_id for c in proceeds.components if c.openmu_item_id is not None]
        slots = self._find_vault_slots(session, command.account_id, physical_ids)
        if slots is None:
            raise PhysicalExecutionError("MARKETPLACE_VAULT_CAPACITY", retryable=True)
        vault_id, _ = self._vault(session, command.account_id)
        numeric_total = 0
        for component in proceeds.components:
            asset = session.get(MarketplacePaymentAsset, component.payment_asset_id)
            if asset is None:
                raise PhysicalExecutionError("MARKETPLACE_ASSET_NOT_FOUND")
            if component.openmu_item_id is None:
                target = self._balance_storage(session, command.account_id, command.character_id, asset)
                limit = self._money_limit(session, asset)
                if target != vault_id:
                    changed = session.execute(text('UPDATE data."ItemStorage" SET "Money"="Money"+:amount WHERE "Id"=:storage AND "Money" >= 0 AND "Money" <= :limit - :amount'), {"amount": component.amount, "storage": target, "limit": limit}).rowcount
                    if changed != 1:
                        raise PhysicalExecutionError("MARKETPLACE_MONEY_CAPACITY", retryable=True)
                else:
                    numeric_total += component.amount
            else:
                self._move_item(session, component.openmu_item_id, vault_id, slots[component.openmu_item_id])
                location = session.get(MarketplaceItemLocation, component.openmu_item_id)
                if location is None or location.location_type != MarketplaceItemLocationType.PROCEEDS:
                    raise PhysicalExecutionError("MARKETPLACE_PROCEEDS_INVARIANT_FAILED")
                session.delete(location)
        if numeric_total:
            limit = self._money_limit(session, None, MarketplaceBalanceScope.ACCOUNT_VAULT)
            changed = session.execute(text('UPDATE data."ItemStorage" SET "Money"="Money"+:amount WHERE "Id"=:storage AND "Money" >= 0 AND "Money" <= :limit - :amount'), {"amount": numeric_total, "storage": vault_id, "limit": limit}).rowcount
            if changed != 1:
                raise PhysicalExecutionError("MARKETPLACE_MONEY_CAPACITY", retryable=True)
        proceeds.status = MarketplaceClaimStatus.CLAIMED
        proceeds.claimed_at = datetime.now(timezone.utc)

    @staticmethod
    def _locked_listing(session: Session, listing_id: uuid.UUID) -> MarketplaceListing:
        listing = session.scalar(select(MarketplaceListing).where(MarketplaceListing.id == listing_id).with_for_update())
        if listing is None:
            raise PhysicalExecutionError("MARKETPLACE_LISTING_NOT_FOUND")
        return listing

    @staticmethod
    def _account_owns_storage(session: Session, account_id: uuid.UUID, storage_id: uuid.UUID | None) -> bool:
        if storage_id is None:
            return False
        return bool(session.execute(text('SELECT EXISTS(SELECT 1 FROM data."Account" a WHERE a."Id"=:account AND a."VaultId"=:storage UNION ALL SELECT 1 FROM data."Character" c WHERE c."AccountId"=:account AND c."InventoryId"=:storage)'), {"account": account_id, "storage": storage_id}).scalar_one())

    @staticmethod
    def _market_storage(session: Session, kind: MarketplaceItemLocationType, reference_id: uuid.UUID, owner: uuid.UUID | None) -> uuid.UUID:
        existing = session.scalar(select(MarketplacePhysicalStorage).where(MarketplacePhysicalStorage.location_type == kind, MarketplacePhysicalStorage.location_reference_id == reference_id))
        if existing:
            return existing.openmu_item_storage_id
        storage_id = uuid.uuid4()
        session.execute(text('INSERT INTO data."ItemStorage" ("Id", "Money") VALUES (:id, 0)'), {"id": storage_id})
        session.add(MarketplacePhysicalStorage(location_type=kind, location_reference_id=reference_id, owner_account_id=owner, openmu_item_storage_id=storage_id))
        session.flush()
        return storage_id

    @staticmethod
    def _move_item(session: Session, item_id: uuid.UUID, storage_id: uuid.UUID, slot: int) -> None:
        if session.execute(text('UPDATE data."Item" SET "ItemStorageId"=:storage, "ItemSlot"=:slot WHERE "Id"=:item'), {"storage": storage_id, "slot": slot, "item": item_id}).rowcount != 1:
            raise PhysicalExecutionError("MARKETPLACE_ITEM_MOVE_FAILED")

    @staticmethod
    def _vault(session: Session, account_id: uuid.UUID) -> tuple[uuid.UUID, bool]:
        row = session.execute(text('SELECT "VaultId", "IsVaultExtended" FROM data."Account" WHERE "Id"=:account FOR UPDATE'), {"account": account_id}).one_or_none()
        if row is None or row.VaultId is None:
            raise PhysicalExecutionError("MARKETPLACE_ACCOUNT_VAULT_MISSING")
        session.execute(text('SELECT "Id" FROM data."ItemStorage" WHERE "Id"=:storage FOR UPDATE'), {"storage": row.VaultId}).one()
        return row.VaultId, row.IsVaultExtended

    def _balance_storage(self, session: Session, account_id: uuid.UUID, character_id: uuid.UUID | None, asset: MarketplacePaymentAsset) -> uuid.UUID:
        scope = asset.balance_scope or MarketplaceBalanceScope.ACCOUNT_VAULT
        if scope == MarketplaceBalanceScope.ACCOUNT_VAULT:
            return self._vault(session, account_id)[0]
        if character_id is None:
            raise PhysicalExecutionError("MARKETPLACE_CHARACTER_REQUIRED")
        storage = session.execute(text('SELECT "InventoryId" FROM data."Character" WHERE "Id"=:character AND "AccountId"=:account FOR UPDATE'), {"character": character_id, "account": account_id}).scalar_one_or_none()
        if storage is None:
            raise PhysicalExecutionError("MARKETPLACE_CHARACTER_NOT_OWNED")
        session.execute(text('SELECT "Id" FROM data."ItemStorage" WHERE "Id"=:storage FOR UPDATE'), {"storage": storage}).one()
        return storage

    @staticmethod
    def _money_limit(session: Session, asset: MarketplacePaymentAsset | None, forced_scope: MarketplaceBalanceScope | None = None) -> int:
        scope = forced_scope or (asset.balance_scope if asset is not None else None) or MarketplaceBalanceScope.ACCOUNT_VAULT
        column = '"MaximumVaultMoney"' if scope == MarketplaceBalanceScope.ACCOUNT_VAULT else '"MaximumInventoryMoney"'
        limit = session.execute(text(f'SELECT MIN({column}) FROM config."GameConfiguration"')).scalar_one_or_none()
        if limit is None or limit < 0:
            raise PhysicalExecutionError("MARKETPLACE_MONEY_LIMIT_UNAVAILABLE", retryable=True)
        return int(limit)

    def _find_vault_slots(self, session: Session, account_id: uuid.UUID, incoming: list[uuid.UUID]) -> dict[uuid.UUID, int] | None:
        vault_id, extended = self._vault(session, account_id)
        rows = 30 if extended else 15
        occupied = [[False] * 8 for _ in range(rows)]
        existing = session.execute(text('SELECT i."Id", i."ItemSlot", d."Width", d."Height" FROM data."Item" i JOIN config."ItemDefinition" d ON d."Id"=i."DefinitionId" WHERE i."ItemStorageId"=:storage FOR UPDATE'), {"storage": vault_id}).all()
        for item in existing:
            if not self._mark(occupied, item.ItemSlot, item.Width, item.Height, reject_overlap=True):
                raise PhysicalExecutionError("MARKETPLACE_VAULT_LAYOUT_INVALID", retryable=True)
        definitions = {r.Id: (r.Width, r.Height) for r in session.execute(text('SELECT i."Id", d."Width", d."Height" FROM data."Item" i JOIN config."ItemDefinition" d ON d."Id"=i."DefinitionId" WHERE i."Id" = ANY(:ids) FOR UPDATE'), {"ids": incoming}).all()} if incoming else {}
        if len(definitions) != len(incoming):
            raise PhysicalExecutionError("MARKETPLACE_ITEM_DEFINITION_MISSING")
        result = {}
        for item_id in incoming:
            width, height = definitions[item_id]
            slot = self._first_fit(occupied, width, height)
            if slot is None:
                return None
            self._mark(occupied, slot, width, height)
            result[item_id] = slot
        return result

    @staticmethod
    def _first_fit(grid, width, height):
        for row in range(len(grid)):
            for col in range(8):
                if row + height <= len(grid) and col + width <= 8 and all(not grid[r][c] for r in range(row, row + height) for c in range(col, col + width)):
                    return row * 8 + col
        return None

    @staticmethod
    def _mark(grid, slot, width, height, reject_overlap=False):
        row, col = divmod(slot, 8)
        if row + height > len(grid) or col + width > 8:
            return False
        if reject_overlap and any(grid[r][c] for r in range(row, row + height) for c in range(col, col + width)):
            return False
        for r in range(row, row + height):
            for c in range(col, col + width):
                grid[r][c] = True
        return True

    @staticmethod
    def _validate_prices(listing: MarketplaceListing) -> None:
        if not listing.price_components:
            raise PhysicalExecutionError("MARKETPLACE_PRICE_REQUIRED")

    @staticmethod
    def _succeed(session: Session, command: MarketplaceCommand) -> None:
        now = datetime.now(timezone.utc)
        command.status = MarketplaceCommandStatus.SUCCEEDED
        command.completed_at = now
        command.failed_at = None
        command.last_error_code = None
        command.blocked_reason_code = None
        command.worker_id = None
        command.worker_lease_expires_at = None
        record = session.scalar(select(MarketplaceIdempotencyRecord).where(MarketplaceIdempotencyRecord.command_id == command.id).with_for_update())
        if record:
            record.response_status = 200
            record.response_body = {"code": "MARKETPLACE_COMMAND_SUCCEEDED", "command_id": str(command.id)}
        session.add(MarketplaceAuditEvent(event_type="MARKETPLACE_COMMAND_SUCCEEDED", correlation_id=command.correlation_id, account_id=command.account_id, listing_id=command.aggregate_id if command.aggregate_type == "listing" else None, command_id=command.id, metadata_json={"command_type": command.command_type.value}))


def process_next_command(session: Session, worker_id: str) -> uuid.UUID | None:
    """Claim and execute one due command in the caller's single transaction."""
    claimed = claim_next_command(session, worker_id)
    if claimed is None:
        return None
    MarketplacePhysicalExecutor().execute(session, claimed.id, worker_id)
    return claimed.id
