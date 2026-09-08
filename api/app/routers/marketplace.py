import uuid

from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import SessionLocal
from app.models.marketplace import (
    MarketplaceCommandType,
    MarketplaceClaimStatus,
    MarketplaceDelivery,
    MarketplaceIdempotencyRecord,
    MarketplaceListing,
    MarketplaceListingPriceComponent,
    MarketplaceListingStatus,
    MarketplacePaymentAsset,
    MarketplaceProceeds,
)
from app.routers.auth import account_from_session
from app.schemas.marketplace import MarketplaceBuyListingInput, MarketplaceClaimInput, MarketplaceCommandSubmissionResponse, MarketplaceCreateListingInput, MarketplaceCreateListingResponse
from app.services.marketplace_domain import IdempotencyConflict, MarketplaceDomainError, create_idempotent_command, validate_price_asset


router = APIRouter(prefix=f"{settings.api_prefix}/marketplace", tags=["marketplace"])
LISTING_ID_NAMESPACE = uuid.UUID("7e57c3ed-9c96-4fd8-9e61-24cd9d4e03f4")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/listings", response_model=MarketplaceCreateListingResponse, status_code=status.HTTP_202_ACCEPTED)
def create_listing(
    payload: MarketplaceCreateListingInput,
    anastaria_session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    account = account_from_session(db, anastaria_session)
    account_id = uuid.UUID(account["id"])
    listing_id = uuid.uuid5(LISTING_ID_NAMESPACE, f"{account_id}:CREATE_LISTING:{payload.idempotency_key}")
    command_payload = {
        "listing_id": str(listing_id),
        "openmu_item_id": str(payload.openmu_item_id),
        "character_id": str(payload.character_id) if payload.character_id else None,
        "price": [component.model_dump(mode="json") for component in payload.price.components],
    }

    listing = db.get(MarketplaceListing, listing_id)
    try:
        if listing is None:
            item = db.execute(text('''
                SELECT i."Id", i."DefinitionId", i."ItemSlot", i."Durability", i."Level",
                       i."HasSkill", i."SocketCount", i."ItemStorageId", d."Name" AS "DefinitionName"
                FROM data."Item" i
                JOIN config."ItemDefinition" d ON d."Id" = i."DefinitionId"
                WHERE i."Id" = :item_id
                  AND EXISTS (
                    SELECT 1 FROM data."Account" a
                    WHERE a."Id" = :account_id AND a."VaultId" = i."ItemStorageId"
                    UNION ALL
                    SELECT 1 FROM data."Character" c
                    WHERE c."AccountId" = :account_id AND c."InventoryId" = i."ItemStorageId"
                  )
            '''), {"item_id": payload.openmu_item_id, "account_id": account_id}).mappings().one_or_none()
            if item is None:
                raise HTTPException(status_code=404, detail="MARKETPLACE_ITEM_NOT_OWNED")

            if payload.character_id is not None:
                owned = db.execute(text('SELECT 1 FROM data."Character" WHERE "Id"=:character_id AND "AccountId"=:account_id'), {
                    "character_id": payload.character_id, "account_id": account_id,
                }).scalar_one_or_none()
                if owned is None:
                    raise HTTPException(status_code=422, detail="MARKETPLACE_CHARACTER_NOT_OWNED")

            assets = {}
            for component in payload.price.components:
                asset = db.get(MarketplacePaymentAsset, component.payment_asset_id)
                if asset is None:
                    raise HTTPException(status_code=422, detail="MARKETPLACE_ASSET_NOT_FOUND")
                validate_price_asset(asset, component.amount)
                assets[asset.id] = asset

            listing = MarketplaceListing(
                id=listing_id,
                seller_account_id=account_id,
                seller_character_id=payload.character_id,
                openmu_item_id=payload.openmu_item_id,
                status=MarketplaceListingStatus.PENDING_ESCROW,
                item_snapshot_version=1,
                item_snapshot={
                    "schema_version": 1,
                    "openmu_item_id": str(item["Id"]),
                    "definition_id": str(item["DefinitionId"]),
                    "definition_name": item["DefinitionName"],
                    "item_level": item["Level"],
                    "durability": item["Durability"],
                    "has_skill": item["HasSkill"],
                    "socket_count": item["SocketCount"],
                },
                version=1,
            )
            db.add(listing)
            db.flush()
            for component in payload.price.components:
                db.add(MarketplaceListingPriceComponent(
                    listing_id=listing.id,
                    payment_asset_id=component.payment_asset_id,
                    amount=component.amount,
                ))

        command, created = create_idempotent_command(
            db,
            account_id=account_id,
            operation=MarketplaceCommandType.CREATE_LISTING,
            idempotency_key=payload.idempotency_key,
            aggregate_type="listing",
            aggregate_id=listing_id,
            payload=command_payload,
            correlation_id=uuid.uuid4(),
            character_id=payload.character_id,
        )
        db.commit()
        db.refresh(listing)
        db.refresh(command)
        return {"listing": listing, "command": command, "created": created}
    except IdempotencyConflict as error:
        db.rollback()
        raise HTTPException(status_code=409, detail=error.code) from error
    except MarketplaceDomainError as error:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(error)) from error
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="MARKETPLACE_LISTING_CONFLICT") from error


@router.post("/listings/{listing_id}/buy", response_model=MarketplaceCommandSubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
def buy_listing(
    listing_id: uuid.UUID,
    payload: MarketplaceBuyListingInput,
    anastaria_session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    account = account_from_session(db, anastaria_session)
    account_id = uuid.UUID(account["id"])
    command_payload = {
        "listing_id": str(listing_id),
        "character_id": str(payload.character_id) if payload.character_id else None,
    }
    existing = db.scalar(select(MarketplaceIdempotencyRecord).where(
        MarketplaceIdempotencyRecord.account_id == account_id,
        MarketplaceIdempotencyRecord.operation == MarketplaceCommandType.BUY_LISTING.value,
        MarketplaceIdempotencyRecord.idempotency_key == payload.idempotency_key,
    ))
    if existing is not None:
        try:
            command, _ = create_idempotent_command(
                db, account_id=account_id, operation=MarketplaceCommandType.BUY_LISTING,
                idempotency_key=payload.idempotency_key, aggregate_type="listing",
                aggregate_id=listing_id, payload=command_payload, correlation_id=uuid.uuid4(),
                character_id=payload.character_id,
            )
            return {"command": command, "created": False}
        except IdempotencyConflict as error:
            raise HTTPException(status_code=409, detail=error.code) from error
    listing = db.get(MarketplaceListing, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="MARKETPLACE_LISTING_NOT_FOUND")
    if listing.seller_account_id == account_id:
        raise HTTPException(status_code=422, detail="MARKETPLACE_BUYER_IS_SELLER")
    if listing.status != MarketplaceListingStatus.ACTIVE:
        raise HTTPException(status_code=409, detail="MARKETPLACE_LISTING_NOT_ACTIVE")
    if payload.character_id is not None:
        owned = db.execute(text('SELECT 1 FROM data."Character" WHERE "Id"=:character_id AND "AccountId"=:account_id'), {
            "character_id": payload.character_id, "account_id": account_id,
        }).scalar_one_or_none()
        if owned is None:
            raise HTTPException(status_code=422, detail="MARKETPLACE_CHARACTER_NOT_OWNED")

    try:
        command, created = create_idempotent_command(
            db,
            account_id=account_id,
            operation=MarketplaceCommandType.BUY_LISTING,
            idempotency_key=payload.idempotency_key,
            aggregate_type="listing",
            aggregate_id=listing_id,
            payload=command_payload,
            correlation_id=uuid.uuid4(),
            character_id=payload.character_id,
        )
        db.commit()
        db.refresh(command)
        return {"command": command, "created": created}
    except IdempotencyConflict as error:
        db.rollback()
        raise HTTPException(status_code=409, detail=error.code) from error


@router.post("/listings/{listing_id}/cancel", response_model=MarketplaceCommandSubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
def cancel_listing(
    listing_id: uuid.UUID,
    payload: MarketplaceClaimInput,
    anastaria_session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    account = account_from_session(db, anastaria_session)
    account_id = uuid.UUID(account["id"])
    command_payload = {"listing_id": str(listing_id)}
    existing = db.scalar(select(MarketplaceIdempotencyRecord).where(
        MarketplaceIdempotencyRecord.account_id == account_id,
        MarketplaceIdempotencyRecord.operation == MarketplaceCommandType.CANCEL_LISTING.value,
        MarketplaceIdempotencyRecord.idempotency_key == payload.idempotency_key,
    ))
    if existing is not None:
        try:
            command, _ = create_idempotent_command(
                db, account_id=account_id, operation=MarketplaceCommandType.CANCEL_LISTING,
                idempotency_key=payload.idempotency_key, aggregate_type="listing",
                aggregate_id=listing_id, payload=command_payload, correlation_id=uuid.uuid4(),
            )
            return {"command": command, "created": False}
        except IdempotencyConflict as error:
            raise HTTPException(status_code=409, detail=error.code) from error

    listing = db.get(MarketplaceListing, listing_id)
    if listing is None or listing.seller_account_id != account_id:
        raise HTTPException(status_code=404, detail="MARKETPLACE_LISTING_NOT_FOUND")
    if listing.status != MarketplaceListingStatus.ACTIVE:
        raise HTTPException(status_code=409, detail="MARKETPLACE_LISTING_NOT_CANCELLABLE")
    command, created = create_idempotent_command(
        db, account_id=account_id, operation=MarketplaceCommandType.CANCEL_LISTING,
        idempotency_key=payload.idempotency_key, aggregate_type="listing",
        aggregate_id=listing_id, payload=command_payload, correlation_id=uuid.uuid4(),
    )
    db.commit()
    db.refresh(command)
    return {"command": command, "created": created}


@router.post("/deliveries/{delivery_id}/claim", response_model=MarketplaceCommandSubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
def claim_delivery(
    delivery_id: uuid.UUID,
    payload: MarketplaceClaimInput,
    anastaria_session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    account = account_from_session(db, anastaria_session)
    account_id = uuid.UUID(account["id"])
    command_payload = {"delivery_id": str(delivery_id)}
    existing = db.scalar(select(MarketplaceIdempotencyRecord).where(
        MarketplaceIdempotencyRecord.account_id == account_id,
        MarketplaceIdempotencyRecord.operation == MarketplaceCommandType.CLAIM_DELIVERY.value,
        MarketplaceIdempotencyRecord.idempotency_key == payload.idempotency_key,
    ))
    if existing is not None:
        try:
            command, _ = create_idempotent_command(
                db, account_id=account_id, operation=MarketplaceCommandType.CLAIM_DELIVERY,
                idempotency_key=payload.idempotency_key, aggregate_type="delivery",
                aggregate_id=delivery_id, payload=command_payload, correlation_id=uuid.uuid4(),
            )
            return {"command": command, "created": False}
        except IdempotencyConflict as error:
            raise HTTPException(status_code=409, detail=error.code) from error

    delivery = db.get(MarketplaceDelivery, delivery_id)
    if delivery is None or delivery.owner_account_id != account_id:
        raise HTTPException(status_code=404, detail="MARKETPLACE_DELIVERY_NOT_FOUND")
    if delivery.status != MarketplaceClaimStatus.PENDING:
        raise HTTPException(status_code=409, detail="MARKETPLACE_DELIVERY_NOT_CLAIMABLE")
    command, created = create_idempotent_command(
        db, account_id=account_id, operation=MarketplaceCommandType.CLAIM_DELIVERY,
        idempotency_key=payload.idempotency_key, aggregate_type="delivery",
        aggregate_id=delivery_id, payload=command_payload, correlation_id=uuid.uuid4(),
    )
    db.commit()
    db.refresh(command)
    return {"command": command, "created": created}


@router.post("/proceeds/{proceeds_id}/claim", response_model=MarketplaceCommandSubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
def claim_proceeds(
    proceeds_id: uuid.UUID,
    payload: MarketplaceClaimInput,
    anastaria_session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    account = account_from_session(db, anastaria_session)
    account_id = uuid.UUID(account["id"])
    command_payload = {"proceeds_id": str(proceeds_id)}
    existing = db.scalar(select(MarketplaceIdempotencyRecord).where(
        MarketplaceIdempotencyRecord.account_id == account_id,
        MarketplaceIdempotencyRecord.operation == MarketplaceCommandType.CLAIM_PROCEEDS.value,
        MarketplaceIdempotencyRecord.idempotency_key == payload.idempotency_key,
    ))
    if existing is not None:
        try:
            command, _ = create_idempotent_command(
                db, account_id=account_id, operation=MarketplaceCommandType.CLAIM_PROCEEDS,
                idempotency_key=payload.idempotency_key, aggregate_type="proceeds",
                aggregate_id=proceeds_id, payload=command_payload, correlation_id=uuid.uuid4(),
            )
            return {"command": command, "created": False}
        except IdempotencyConflict as error:
            raise HTTPException(status_code=409, detail=error.code) from error

    proceeds = db.get(MarketplaceProceeds, proceeds_id)
    if proceeds is None or proceeds.owner_account_id != account_id:
        raise HTTPException(status_code=404, detail="MARKETPLACE_PROCEEDS_NOT_FOUND")
    if proceeds.status != MarketplaceClaimStatus.PENDING:
        raise HTTPException(status_code=409, detail="MARKETPLACE_PROCEEDS_NOT_CLAIMABLE")
    command, created = create_idempotent_command(
        db, account_id=account_id, operation=MarketplaceCommandType.CLAIM_PROCEEDS,
        idempotency_key=payload.idempotency_key, aggregate_type="proceeds",
        aggregate_id=proceeds_id, payload=command_payload, correlation_id=uuid.uuid4(),
    )
    db.commit()
    db.refresh(command)
    return {"command": command, "created": created}
