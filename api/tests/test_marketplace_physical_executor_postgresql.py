import uuid
import threading
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.engine import engine
from app.models.marketplace import (
    MarketplaceAssetType, MarketplaceBalanceScope, MarketplaceClaimStatus,
    MarketplaceAccountReconciliation, MarketplaceAuditEvent, MarketplaceDelivery,
    MarketplaceCommand, MarketplaceCommandStatus, MarketplaceCommandType,
    MarketplaceItemLocation, MarketplaceItemLocationType,
    MarketplaceListing, MarketplaceListingPriceComponent, MarketplaceListingStatus,
    MarketplacePaymentAsset, MarketplaceProceeds, MarketplaceSessionKind,
    MarketplaceSessionState, MarketplaceAccountSession,
)
from app.services.marketplace_domain import claim_next_command
from app.services.marketplace_executor import MarketplacePhysicalExecutor

pytestmark = pytest.mark.skipif(engine.dialect.name != "postgresql", reason="requires PostgreSQL")


def add_account(session, account_id, vault_id, money):
    session.execute(text('INSERT INTO data."ItemStorage" ("Id","Money") VALUES (:v,:m)'), {"v": vault_id, "m": money})
    session.execute(text('''INSERT INTO data."Account"
        ("Id","VaultId","LoginName","PasswordHash","SecurityCode","EMail","RegistrationDate","State","TimeZone","VaultPassword","IsVaultExtended","ChatBanUntil","IsTemplate","LanguageIsoCode","IsBot")
        VALUES (:id,:vault,:login,'x','','',now(),0,0,'',false,NULL,false,'en',false)'''),
        {"id": account_id, "vault": vault_id, "login": uuid.uuid4().hex[:10]})


def add_item(session, item_id, storage_id, definition_id, slot=0):
    session.execute(text('''INSERT INTO data."Item"
        ("Id","ItemStorageId","DefinitionId","ItemSlot","Durability","Level","HasSkill","SocketCount","StorePrice","PetExperience")
        VALUES (:id,:storage,:definition,:slot,1,0,false,0,NULL,0)'''),
        {"id": item_id, "storage": storage_id, "definition": definition_id, "slot": slot})


def add_character(session, character_id, account_id, inventory_id, name):
    character_class = session.execute(text('SELECT "Id" FROM config."CharacterClass" LIMIT 1')).scalar_one()
    session.execute(text('''INSERT INTO data."Character"
        ("Id","CharacterClassId","InventoryId","AccountId","Name","CharacterSlot","CreateDate","Experience","MasterExperience","LevelUpPoints","MasterLevelUpPoints","PositionX","PositionY","PlayerKillCount","StateRemainingSeconds","State","CharacterStatus","Pose","UsedFruitPoints","UsedNegFruitPoints","InventoryExtensions","IsStoreOpened")
        VALUES (:id,:class,:inventory,:account,:name,0,now(),0,0,0,0,0,0,0,0,0,0,0,0,0,0,false)'''),
        {"id": character_id, "class": character_class, "inventory": inventory_id, "account": account_id, "name": name})


def command(session, kind, account_id, aggregate_id, worker="pytest"):
    value = MarketplaceCommand(command_type=kind, aggregate_type="listing" if "LISTING" in kind.value else "claim", aggregate_id=aggregate_id, account_id=account_id, idempotency_key=str(uuid.uuid4()), payload={}, payload_hash="0" * 64, status=MarketplaceCommandStatus.PROCESSING, worker_id=worker, worker_lease_expires_at=datetime.now(timezone.utc) + timedelta(minutes=2), correlation_id=uuid.uuid4())
    session.add(value); session.flush(); return value


@pytest.fixture
def physical_world():
    ids = {name: uuid.uuid4() for name in ("seller", "buyer", "buyer2", "seller_vault", "buyer_vault", "buyer2_vault", "seller_inventory", "buyer_inventory", "buyer2_inventory", "seller_character", "buyer_character", "buyer2_character", "item")}
    with Session(engine) as session, session.begin():
        definition = session.execute(text('SELECT "Id" FROM config."ItemDefinition" WHERE "Width" <= 8 AND "Height" <= 15 LIMIT 1')).scalar_one()
        ids["definition"] = definition
        add_account(session, ids["seller"], ids["seller_vault"], 0)
        add_account(session, ids["buyer"], ids["buyer_vault"], 1000)
        add_account(session, ids["buyer2"], ids["buyer2_vault"], 1000)
        for storage in (ids["seller_inventory"], ids["buyer_inventory"], ids["buyer2_inventory"]):
            session.execute(text('INSERT INTO data."ItemStorage" ("Id","Money") VALUES (:id,1000)'), {"id": storage})
        add_character(session, ids["seller_character"], ids["seller"], ids["seller_inventory"], f"s{ids['seller'].hex[:9]}")
        add_character(session, ids["buyer_character"], ids["buyer"], ids["buyer_inventory"], f"b{ids['buyer'].hex[:9]}")
        add_character(session, ids["buyer2_character"], ids["buyer2"], ids["buyer2_inventory"], f"o{ids['buyer2'].hex[:9]}")
        add_item(session, ids["item"], ids["seller_vault"], definition)
    yield ids
    with Session(engine) as session, session.begin():
        market_storages = session.execute(text('SELECT openmu_item_storage_id FROM marketplace_physical_storages WHERE owner_account_id IN (:seller,:buyer,:buyer2)'), ids).scalars().all()
        session.execute(text('DELETE FROM data."Item" WHERE "ItemStorageId" IN (:sv,:bv,:b2v) OR "ItemStorageId" = ANY(:market)'), {"sv": ids["seller_vault"], "bv": ids["buyer_vault"], "b2v": ids["buyer2_vault"], "market": market_storages or [uuid.uuid4()]})
        session.execute(text('DELETE FROM marketplace_account_sessions WHERE account_id IN (:seller,:buyer,:buyer2)'), ids)
        session.execute(text('DELETE FROM marketplace_account_reconciliations WHERE account_id IN (:seller,:buyer,:buyer2)'), ids)
        session.execute(text('DELETE FROM marketplace_audit_events WHERE account_id IN (:seller,:buyer,:buyer2)'), ids)
        session.execute(text('DELETE FROM marketplace_idempotency WHERE account_id IN (:seller,:buyer,:buyer2)'), ids)
        session.execute(text('DELETE FROM marketplace_commands WHERE account_id IN (:seller,:buyer,:buyer2)'), ids)
        session.execute(text('DELETE FROM marketplace_item_locations WHERE owner_account_id IN (:seller,:buyer,:buyer2)'), ids)
        session.execute(text('DELETE FROM marketplace_proceeds_components WHERE proceeds_id IN (SELECT id FROM marketplace_proceeds WHERE owner_account_id IN (:seller,:buyer,:buyer2))'), ids)
        session.execute(text('DELETE FROM marketplace_deliveries WHERE owner_account_id IN (:seller,:buyer,:buyer2)'), ids)
        session.execute(text('DELETE FROM marketplace_proceeds WHERE owner_account_id IN (:seller,:buyer,:buyer2)'), ids)
        session.execute(text('DELETE FROM marketplace_transactions WHERE seller_account_id=:seller OR buyer_account_id IN (:buyer,:buyer2)'), ids)
        session.execute(text('DELETE FROM marketplace_listing_price_components WHERE listing_id IN (SELECT id FROM marketplace_listings WHERE seller_account_id=:seller)'), ids)
        session.execute(text('DELETE FROM marketplace_listings WHERE seller_account_id=:seller'), ids)
        session.execute(text('DELETE FROM marketplace_payment_assets WHERE code LIKE :code'), {"code": f"PYTEST-{ids['seller']}%"})
        session.execute(text('DELETE FROM marketplace_physical_storages WHERE owner_account_id IN (:seller,:buyer,:buyer2)'), ids)
        session.execute(text('DELETE FROM marketplace_account_fences WHERE account_id IN (:seller,:buyer,:buyer2)'), ids)
        session.execute(text('DELETE FROM data."Character" WHERE "Id" IN (:seller_character,:buyer_character,:buyer2_character)'), ids)
        session.execute(text('DELETE FROM data."Account" WHERE "Id" IN (:seller,:buyer,:buyer2)'), ids)
        if market_storages:
            session.execute(text('DELETE FROM data."ItemStorage" WHERE "Id" IN (:sv,:bv,:b2v) OR "Id" = ANY(:market)'), {"sv": ids["seller_vault"], "bv": ids["buyer_vault"], "b2v": ids["buyer2_vault"], "market": market_storages})
        else:
            session.execute(text('DELETE FROM data."ItemStorage" WHERE "Id" IN (:sv,:bv,:b2v)'), {"sv": ids["seller_vault"], "bv": ids["buyer_vault"], "b2v": ids["buyer2_vault"]})
        session.execute(text('DELETE FROM data."ItemStorage" WHERE "Id" IN (:seller_inventory,:buyer_inventory,:buyer2_inventory)'), ids)


def test_create_buy_and_claim_preserve_item_and_numeric_exactly_once(physical_world):
    x = physical_world
    executor = MarketplacePhysicalExecutor()
    with Session(engine) as session, session.begin():
        asset = MarketplacePaymentAsset(code=f"PYTEST-{x['seller']}-ZEN", asset_type=MarketplaceAssetType.NUMERIC_BALANCE, balance_scope=MarketplaceBalanceScope.ACCOUNT_VAULT, display_name_key="test", min_amount=1)
        listing = MarketplaceListing(seller_account_id=x["seller"], openmu_item_id=x["item"], status=MarketplaceListingStatus.PENDING_ESCROW, item_snapshot_version=1, item_snapshot={"schema_version": 1}, version=1)
        session.add_all([asset, listing]); session.flush()
        session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=asset.id, amount=125)); session.flush()
        create = command(session, MarketplaceCommandType.CREATE_LISTING, x["seller"], listing.id)
        executor.execute(session, create.id, "pytest")
        assert create.status == MarketplaceCommandStatus.SUCCEEDED
        assert session.execute(text('SELECT "Id" FROM data."Item" WHERE "Id"=:id'), {"id": x["item"]}).scalar_one() == x["item"]

        buy = command(session, MarketplaceCommandType.BUY_LISTING, x["buyer"], listing.id)
        executor.execute(session, buy.id, "pytest")
        assert listing.status == MarketplaceListingStatus.SOLD
        assert session.execute(text('SELECT "Money" FROM data."ItemStorage" WHERE "Id"=:id'), {"id": x["buyer_vault"]}).scalar_one() == 875
        delivery = session.query(__import__('app.models.marketplace', fromlist=['MarketplaceDelivery']).MarketplaceDelivery).filter_by(owner_account_id=x["buyer"]).one()
        claim_delivery = command(session, MarketplaceCommandType.CLAIM_DELIVERY, x["buyer"], delivery.id)
        executor.execute(session, claim_delivery.id, "pytest")
        assert delivery.status == MarketplaceClaimStatus.CLAIMED
        assert session.execute(text('SELECT "ItemStorageId" FROM data."Item" WHERE "Id"=:id'), {"id": x["item"]}).scalar_one() == x["buyer_vault"]
        proceeds = session.query(MarketplaceProceeds).filter_by(owner_account_id=x["seller"]).one()
        claim_proceeds = command(session, MarketplaceCommandType.CLAIM_PROCEEDS, x["seller"], proceeds.id)
        executor.execute(session, claim_proceeds.id, "pytest")
        assert session.execute(text('SELECT "Money" FROM data."ItemStorage" WHERE "Id"=:id'), {"id": x["seller_vault"]}).scalar_one() == 125
        executor.execute(session, claim_proceeds.id, "pytest")
        assert session.execute(text('SELECT "Money" FROM data."ItemStorage" WHERE "Id"=:id'), {"id": x["seller_vault"]}).scalar_one() == 125


def test_online_session_blocks_without_moving_item(physical_world):
    x = physical_world
    with Session(engine) as session, session.begin():
        listing = MarketplaceListing(seller_account_id=x["seller"], openmu_item_id=x["item"], status=MarketplaceListingStatus.PENDING_ESCROW, item_snapshot_version=1, item_snapshot={}, version=1)
        asset = MarketplacePaymentAsset(code=f"PYTEST-{x['seller']}-BLOCK", asset_type=MarketplaceAssetType.NUMERIC_BALANCE, balance_scope=MarketplaceBalanceScope.ACCOUNT_VAULT, display_name_key="test", min_amount=1)
        session.add_all([listing, asset]); session.flush(); session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=asset.id, amount=1))
        now = datetime.now(timezone.utc)
        session.add(MarketplaceAccountSession(account_id=x["seller"], session_id=uuid.uuid4(), session_kind=MarketplaceSessionKind.ONLINE, game_server_instance_id="pytest", fencing_token=1, state=MarketplaceSessionState.ACTIVE, heartbeat_at=now, lease_expires_at=now + timedelta(minutes=2)))
        cmd = command(session, MarketplaceCommandType.CREATE_LISTING, x["seller"], listing.id)
        MarketplacePhysicalExecutor().execute(session, cmd.id, "pytest")
        assert cmd.status == MarketplaceCommandStatus.RETRYABLE_FAILED
        assert session.execute(text('SELECT "ItemStorageId" FROM data."Item" WHERE "Id"=:id'), {"id": x["item"]}).scalar_one() == x["seller_vault"]
        session.query(MarketplaceAccountSession).filter_by(account_id=x["seller"]).delete()
        cmd.status = MarketplaceCommandStatus.PROCESSING
        cmd.worker_id = "pytest"
        MarketplacePhysicalExecutor().execute(session, cmd.id, "pytest")
        assert cmd.status == MarketplaceCommandStatus.SUCCEEDED
        assert cmd.last_error_code is None
        assert cmd.failed_at is None


def test_rollback_after_physical_move_restores_original_storage(physical_world):
    x = physical_world
    listing_id = uuid.uuid4()
    with pytest.raises(RuntimeError):
        with Session(engine) as session, session.begin():
            asset = MarketplacePaymentAsset(code=f"PYTEST-{x['seller']}-ROLLBACK", asset_type=MarketplaceAssetType.NUMERIC_BALANCE, balance_scope=MarketplaceBalanceScope.ACCOUNT_VAULT, display_name_key="test", min_amount=1)
            listing = MarketplaceListing(id=listing_id, seller_account_id=x["seller"], openmu_item_id=x["item"], status=MarketplaceListingStatus.PENDING_ESCROW, item_snapshot_version=1, item_snapshot={}, version=1)
            session.add_all([asset, listing]); session.flush(); session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=asset.id, amount=1)); session.flush()
            cmd = command(session, MarketplaceCommandType.CREATE_LISTING, x["seller"], listing.id)
            MarketplacePhysicalExecutor().execute(session, cmd.id, "pytest")
            raise RuntimeError("fault injection before commit")
    with Session(engine) as session:
        assert session.execute(text('SELECT "ItemStorageId" FROM data."Item" WHERE "Id"=:id'), {"id": x["item"]}).scalar_one() == x["seller_vault"]
        assert session.get(MarketplaceListing, listing_id) is None


def test_physical_composite_payment_preserves_every_item_id(physical_world):
    x = physical_world
    payments = [uuid.uuid4(), uuid.uuid4()]
    executor = MarketplacePhysicalExecutor()
    with Session(engine) as session, session.begin():
        for slot, item_id in enumerate(payments, 10):
            add_item(session, item_id, x["buyer_vault"], x["definition"], slot)
        asset = MarketplacePaymentAsset(code=f"PYTEST-{x['seller']}-PHYSICAL", asset_type=MarketplaceAssetType.PHYSICAL_ITEM, balance_scope=None, openmu_item_definition_id=x["definition"], display_name_key="test", min_amount=1)
        listing = MarketplaceListing(seller_account_id=x["seller"], openmu_item_id=x["item"], status=MarketplaceListingStatus.PENDING_ESCROW, item_snapshot_version=1, item_snapshot={}, version=1)
        session.add_all([asset, listing]); session.flush(); session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=asset.id, amount=2)); session.flush()
        create = command(session, MarketplaceCommandType.CREATE_LISTING, x["seller"], listing.id)
        executor.execute(session, create.id, "pytest")
        buy = command(session, MarketplaceCommandType.BUY_LISTING, x["buyer"], listing.id)
        executor.execute(session, buy.id, "pytest")
        proceeds = session.query(MarketplaceProceeds).filter_by(owner_account_id=x["seller"]).one()
        assert {component.openmu_item_id for component in proceeds.components} == set(payments)
        assert session.execute(text('SELECT COUNT(DISTINCT "Id") FROM data."Item" WHERE "Id" = ANY(:ids)'), {"ids": payments}).scalar_one() == 2
        claim = command(session, MarketplaceCommandType.CLAIM_PROCEEDS, x["seller"], proceeds.id)
        executor.execute(session, claim.id, "pytest")
        moved = set(session.execute(text('SELECT "Id" FROM data."Item" WHERE "ItemStorageId"=:vault AND "Id" = ANY(:ids)'), {"vault": x["seller_vault"], "ids": payments}).scalars())
        assert moved == set(payments)


def test_physical_payment_selects_lowest_eligible_item_ids_deterministically(physical_world):
    x = physical_world
    payments = sorted([uuid.uuid4(), uuid.uuid4(), uuid.uuid4()])
    with Session(engine) as session, session.begin():
        for slot, item_id in enumerate(reversed(payments), 10):
            add_item(session, item_id, x["buyer_vault"], x["definition"], slot)
        asset = MarketplacePaymentAsset(code=f"PYTEST-{x['seller'].hex[:12]}-ORDER", asset_type=MarketplaceAssetType.PHYSICAL_ITEM, openmu_item_definition_id=x["definition"], display_name_key="test", min_amount=1)
        listing = MarketplaceListing(seller_account_id=x["seller"], openmu_item_id=x["item"], status=MarketplaceListingStatus.PENDING_ESCROW, item_snapshot_version=1, item_snapshot={}, version=1)
        session.add_all([asset, listing]); session.flush()
        session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=asset.id, amount=2)); session.flush()
        executor = MarketplacePhysicalExecutor()
        create = command(session, MarketplaceCommandType.CREATE_LISTING, x["seller"], listing.id); executor.execute(session, create.id, "pytest")
        buy = command(session, MarketplaceCommandType.BUY_LISTING, x["buyer"], listing.id); executor.execute(session, buy.id, "pytest")
        proceeds = session.query(MarketplaceProceeds).filter_by(owner_account_id=x["seller"]).one()
        assert {component.openmu_item_id for component in proceeds.components} == set(payments[:2])
        assert session.execute(text('SELECT "ItemStorageId" FROM data."Item" WHERE "Id"=:id'), {"id": payments[2]}).scalar_one() == x["buyer_vault"]


@pytest.mark.parametrize("location_type", list(MarketplaceItemLocationType))
def test_marketplace_managed_item_cannot_be_reused_as_physical_payment(physical_world, location_type):
    x = physical_world
    managed, eligible = uuid.uuid4(), uuid.uuid4()
    with Session(engine) as session, session.begin():
        add_item(session, managed, x["buyer_vault"], x["definition"], 10)
        add_item(session, eligible, x["buyer_vault"], x["definition"], 11)
        session.add(MarketplaceItemLocation(openmu_item_id=managed, location_type=location_type, location_reference_id=uuid.uuid4(), owner_account_id=x["buyer"], fencing_token=1, origin_storage_id=x["buyer_vault"], origin_item_slot=10))
        asset = MarketplacePaymentAsset(code=f"PYTEST-{x['seller'].hex[:8]}-{location_type.value}", asset_type=MarketplaceAssetType.PHYSICAL_ITEM, openmu_item_definition_id=x["definition"], display_name_key="test", min_amount=1)
        listing = MarketplaceListing(seller_account_id=x["seller"], openmu_item_id=x["item"], status=MarketplaceListingStatus.PENDING_ESCROW, item_snapshot_version=1, item_snapshot={}, version=1)
        session.add_all([asset, listing]); session.flush()
        session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=asset.id, amount=1)); session.flush()
        executor = MarketplacePhysicalExecutor()
        create = command(session, MarketplaceCommandType.CREATE_LISTING, x["seller"], listing.id); executor.execute(session, create.id, "pytest")
        buy = command(session, MarketplaceCommandType.BUY_LISTING, x["buyer"], listing.id); executor.execute(session, buy.id, "pytest")
        proceeds = session.query(MarketplaceProceeds).filter_by(owner_account_id=x["seller"]).one()
        assert {component.openmu_item_id for component in proceeds.components} == {eligible}
        assert session.execute(text('SELECT "ItemStorageId" FROM data."Item" WHERE "Id"=:id'), {"id": managed}).scalar_one() == x["buyer_vault"]


def test_insufficient_physical_component_rolls_back_everything(physical_world):
    x = physical_world
    payment = uuid.uuid4()
    listing_id = uuid.uuid4()
    with Session(engine) as session, session.begin():
        add_item(session, payment, x["buyer_vault"], x["definition"], 10)
        asset = MarketplacePaymentAsset(code=f"PYTEST-{x['seller']}-SHORT", asset_type=MarketplaceAssetType.PHYSICAL_ITEM, balance_scope=None, openmu_item_definition_id=x["definition"], display_name_key="test", min_amount=1)
        listing = MarketplaceListing(id=listing_id, seller_account_id=x["seller"], openmu_item_id=x["item"], status=MarketplaceListingStatus.PENDING_ESCROW, item_snapshot_version=1, item_snapshot={}, version=1)
        session.add_all([asset, listing]); session.flush(); session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=asset.id, amount=2)); session.flush()
        create = command(session, MarketplaceCommandType.CREATE_LISTING, x["seller"], listing.id)
        MarketplacePhysicalExecutor().execute(session, create.id, "pytest")
    with pytest.raises(Exception, match="MARKETPLACE_INSUFFICIENT_PHYSICAL_BALANCE"):
        with Session(engine) as session, session.begin():
            buy = command(session, MarketplaceCommandType.BUY_LISTING, x["buyer"], listing_id)
            MarketplacePhysicalExecutor().execute(session, buy.id, "pytest")
    with Session(engine) as session:
        assert session.execute(text('SELECT "ItemStorageId" FROM data."Item" WHERE "Id"=:id'), {"id": payment}).scalar_one() == x["buyer_vault"]
        assert session.get(MarketplaceListing, listing_id).status == MarketplaceListingStatus.ACTIVE


@pytest.mark.parametrize("second_kind", [MarketplaceCommandType.BUY_LISTING, MarketplaceCommandType.CANCEL_LISTING])
def test_competing_buy_or_cancel_has_exactly_one_winner(physical_world, second_kind):
    x = physical_world
    with Session(engine) as session, session.begin():
        asset = MarketplacePaymentAsset(code=f"PYTEST-{x['seller']}-RACE-{second_kind.value}", asset_type=MarketplaceAssetType.NUMERIC_BALANCE, balance_scope=MarketplaceBalanceScope.ACCOUNT_VAULT, display_name_key="test", min_amount=1)
        listing = MarketplaceListing(seller_account_id=x["seller"], openmu_item_id=x["item"], status=MarketplaceListingStatus.PENDING_ESCROW, item_snapshot_version=1, item_snapshot={}, version=1)
        session.add_all([asset, listing]); session.flush(); session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=asset.id, amount=10)); session.flush()
        create = command(session, MarketplaceCommandType.CREATE_LISTING, x["seller"], listing.id)
        MarketplacePhysicalExecutor().execute(session, create.id, "pytest")
        first = command(session, MarketplaceCommandType.BUY_LISTING, x["buyer"], listing.id, "race-a")
        second_account = x["buyer2"] if second_kind == MarketplaceCommandType.BUY_LISTING else x["seller"]
        second = command(session, second_kind, second_account, listing.id, "race-b")
        listing_id, command_ids = listing.id, (first.id, second.id)

    barrier = threading.Barrier(2)
    outcomes = []
    def run(command_id, worker):
        try:
            with Session(engine) as session, session.begin():
                barrier.wait(5)
                MarketplacePhysicalExecutor().execute(session, command_id, worker)
            outcomes.append("success")
        except Exception:
            outcomes.append("lost")
    threads = [threading.Thread(target=run, args=(command_ids[0], "race-a")), threading.Thread(target=run, args=(command_ids[1], "race-b"))]
    [thread.start() for thread in threads]
    [thread.join(10) for thread in threads]
    assert outcomes.count("success") == 1
    with Session(engine) as session:
        assert session.get(MarketplaceListing, listing_id).status in (MarketplaceListingStatus.SOLD, MarketplaceListingStatus.CANCELLED)
        assert sum(session.get(MarketplaceCommand, value).status == MarketplaceCommandStatus.SUCCEEDED for value in command_ids) == 1


def test_full_vault_leaves_delivery_untouched_and_retryable(physical_world):
    x = physical_world
    fillers = [uuid.uuid4() for _ in range(120)]
    with Session(engine) as session, session.begin():
        one_by_one = session.execute(text('SELECT "Id" FROM config."ItemDefinition" WHERE "Width"=1 AND "Height"=1 LIMIT 1')).scalar_one()
        for slot, item_id in enumerate(fillers):
            add_item(session, item_id, x["buyer_vault"], one_by_one, slot)
        asset = MarketplacePaymentAsset(code=f"PYTEST-{x['seller']}-FULL", asset_type=MarketplaceAssetType.NUMERIC_BALANCE, balance_scope=MarketplaceBalanceScope.ACCOUNT_VAULT, display_name_key="test", min_amount=1)
        listing = MarketplaceListing(seller_account_id=x["seller"], openmu_item_id=x["item"], status=MarketplaceListingStatus.PENDING_ESCROW, item_snapshot_version=1, item_snapshot={}, version=1)
        session.add_all([asset, listing]); session.flush(); session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=asset.id, amount=1)); session.flush()
        executor = MarketplacePhysicalExecutor()
        create = command(session, MarketplaceCommandType.CREATE_LISTING, x["seller"], listing.id); executor.execute(session, create.id, "pytest")
        buy = command(session, MarketplaceCommandType.BUY_LISTING, x["buyer"], listing.id); executor.execute(session, buy.id, "pytest")
        delivery = session.query(__import__('app.models.marketplace', fromlist=['MarketplaceDelivery']).MarketplaceDelivery).filter_by(owner_account_id=x["buyer"]).one()
        market_storage = session.execute(text('SELECT "ItemStorageId" FROM data."Item" WHERE "Id"=:item'), {"item": x["item"]}).scalar_one()
        claim = command(session, MarketplaceCommandType.CLAIM_DELIVERY, x["buyer"], delivery.id)
        executor.execute(session, claim.id, "pytest")
        assert claim.status == MarketplaceCommandStatus.RETRYABLE_FAILED
        assert claim.last_error_code == "MARKETPLACE_VAULT_CAPACITY"
        assert delivery.status == MarketplaceClaimStatus.PENDING
        assert session.execute(text('SELECT "ItemStorageId" FROM data."Item" WHERE "Id"=:item'), {"item": x["item"]}).scalar_one() == market_storage


def test_vault_first_fit_matches_openmu_row_major_geometry():
    executor = MarketplacePhysicalExecutor()
    grid = [[False] * 8 for _ in range(15)]
    assert executor._mark(grid, 0, 2, 2)
    assert executor._mark(grid, 2, 1, 1)
    assert executor._first_fit(grid, 2, 2) == 3
    assert executor._mark(grid, 3, 2, 2)
    assert not executor._mark(grid, 7, 2, 1)
    assert not executor._mark(grid, 14 * 8, 1, 2)
    assert executor._first_fit(grid, 8, 1) == 16


def test_vault_geometry_enforces_boundaries_non_overlap_and_capacity():
    executor = MarketplacePhysicalExecutor()
    grid = [[False] * 8 for _ in range(15)]
    assert executor._mark(grid, 6, 2, 2, reject_overlap=True)
    assert not executor._mark(grid, 7, 1, 2, reject_overlap=True)
    assert executor._mark(grid, 14 * 8 + 6, 2, 1, reject_overlap=True)
    assert not executor._mark(grid, 14 * 8 + 7, 2, 1, reject_overlap=True)
    full = [[True] * 8 for _ in range(15)]
    assert executor._first_fit(full, 1, 1) is None
    extended = [[True] * 8 for _ in range(30)]
    extended[29][7] = False
    assert executor._first_fit(extended, 1, 1) == 239


def prepare_physical_command(session, x, kind):
    executor = MarketplacePhysicalExecutor()
    asset = MarketplacePaymentAsset(code=f"PYTEST-{x['seller'].hex[:12]}-{kind.value}", asset_type=MarketplaceAssetType.NUMERIC_BALANCE, balance_scope=MarketplaceBalanceScope.ACCOUNT_VAULT, display_name_key="test", min_amount=1)
    listing = MarketplaceListing(seller_account_id=x["seller"], openmu_item_id=x["item"], status=MarketplaceListingStatus.PENDING_ESCROW, item_snapshot_version=1, item_snapshot={}, version=1)
    session.add_all([asset, listing]); session.flush()
    session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=asset.id, amount=10)); session.flush()
    if kind == MarketplaceCommandType.CREATE_LISTING:
        return command(session, kind, x["seller"], listing.id), listing
    create = command(session, MarketplaceCommandType.CREATE_LISTING, x["seller"], listing.id)
    executor.execute(session, create.id, "pytest")
    if kind == MarketplaceCommandType.CANCEL_LISTING:
        return command(session, kind, x["seller"], listing.id), listing
    buy = command(session, MarketplaceCommandType.BUY_LISTING, x["buyer"], listing.id)
    if kind == MarketplaceCommandType.BUY_LISTING:
        return buy, listing
    executor.execute(session, buy.id, "pytest")
    if kind == MarketplaceCommandType.CLAIM_DELIVERY:
        delivery = session.query(MarketplaceDelivery).filter_by(owner_account_id=x["buyer"]).one()
        return command(session, kind, x["buyer"], delivery.id), listing
    proceeds = session.query(MarketplaceProceeds).filter_by(owner_account_id=x["seller"]).one()
    return command(session, kind, x["seller"], proceeds.id), listing


def economic_snapshot(session, x, listing):
    return {
        "item_storage": session.execute(text('SELECT "ItemStorageId" FROM data."Item" WHERE "Id"=:id'), {"id": x["item"]}).scalar_one(),
        "seller_money": session.execute(text('SELECT "Money" FROM data."ItemStorage" WHERE "Id"=:id'), {"id": x["seller_vault"]}).scalar_one(),
        "buyer_money": session.execute(text('SELECT "Money" FROM data."ItemStorage" WHERE "Id"=:id'), {"id": x["buyer_vault"]}).scalar_one(),
        "listing_status": listing.status,
        "transactions": session.execute(text('SELECT count(*) FROM marketplace_transactions WHERE listing_id=:id'), {"id": listing.id}).scalar_one(),
        "delivery_states": tuple(session.execute(text('SELECT status FROM marketplace_deliveries WHERE source_transaction_id IN (SELECT id FROM marketplace_transactions WHERE listing_id=:id) ORDER BY id'), {"id": listing.id}).scalars()),
        "proceeds_states": tuple(session.execute(text('SELECT status FROM marketplace_proceeds WHERE source_transaction_id IN (SELECT id FROM marketplace_transactions WHERE listing_id=:id) ORDER BY id'), {"id": listing.id}).scalars()),
    }


BLOCKED_SESSION_CASES = [
    ("starting", MarketplaceSessionState.STARTING, MarketplaceSessionKind.ONLINE, False),
    ("active_online", MarketplaceSessionState.ACTIVE, MarketplaceSessionKind.ONLINE, False),
    ("active_offline_helper", MarketplaceSessionState.ACTIVE, MarketplaceSessionKind.OFFLINE_HELPER, False),
    ("stopping", MarketplaceSessionState.STOPPING, MarketplaceSessionKind.ONLINE, False),
    ("expired_unreconciled", MarketplaceSessionState.ACTIVE, MarketplaceSessionKind.ONLINE, True),
]


@pytest.mark.parametrize("kind", list(MarketplaceCommandType))
@pytest.mark.parametrize("case,state,session_kind,expired", BLOCKED_SESSION_CASES)
def test_every_physical_command_is_retryable_without_mutation_for_unsafe_session(physical_world, kind, case, state, session_kind, expired):
    x = physical_world
    with Session(engine) as session, session.begin():
        cmd, listing = prepare_physical_command(session, x, kind)
        account_id = cmd.account_id
        now = datetime.now(timezone.utc)
        session.add(MarketplaceAccountSession(
            account_id=account_id, session_id=uuid.uuid4(), session_kind=session_kind,
            game_server_instance_id="pytest-matrix", fencing_token=1, state=state,
            heartbeat_at=now - (timedelta(minutes=5) if expired else timedelta()),
            lease_expires_at=now - timedelta(minutes=1) if expired else now + timedelta(minutes=2),
        ))
        session.flush()
        before = economic_snapshot(session, x, listing)
        MarketplacePhysicalExecutor().execute(session, cmd.id, "pytest")
        assert economic_snapshot(session, x, listing) == before, (kind, case)
        assert cmd.status == MarketplaceCommandStatus.RETRYABLE_FAILED
        assert cmd.blocked_reason_code == "MARKETPLACE_SESSION_PRESENT"
        assert cmd.available_at > now
        assert cmd.worker_id is None and cmd.worker_lease_expires_at is None
        session.flush()
        events = session.scalars(text('SELECT event_type FROM marketplace_audit_events WHERE command_id=:id'), {"id": cmd.id}).all()
        assert "MARKETPLACE_COMMAND_BLOCKED_ACCOUNT_UNSAFE" in events
        assert "MARKETPLACE_COMMAND_SUCCEEDED" not in events
        if expired:
            assert session.get(MarketplaceAccountReconciliation, account_id) is not None


@pytest.mark.parametrize("kind", list(MarketplaceCommandType))
def test_every_physical_command_allows_reconciled_safe_offline(physical_world, kind):
    x = physical_world
    with Session(engine) as session, session.begin():
        cmd, listing = prepare_physical_command(session, x, kind)
        session.add(MarketplaceAccountReconciliation(
            account_id=cmd.account_id, required_fencing_token=3,
            required_reason_code="pytest", required_at=datetime.now(timezone.utc),
            reconciled_fencing_token=3, reconciled_at=datetime.now(timezone.utc), reconciled_by="pytest",
        ))
        MarketplacePhysicalExecutor().execute(session, cmd.id, "pytest")
        assert cmd.status == MarketplaceCommandStatus.SUCCEEDED


@pytest.mark.parametrize("character_key,error_code", [
    (None, "MARKETPLACE_CHARACTER_REQUIRED"),
    ("missing", "MARKETPLACE_CHARACTER_NOT_OWNED"),
    ("buyer2_character", "MARKETPLACE_CHARACTER_NOT_OWNED"),
])
def test_character_inventory_debit_rejects_missing_or_unowned_character_without_fallback(physical_world, character_key, error_code):
    x = physical_world
    with Session(engine) as session, session.begin():
        asset = MarketplacePaymentAsset(code=f"PYTEST-{x['seller'].hex[:12]}-CHAR-REJECT-{character_key}", asset_type=MarketplaceAssetType.NUMERIC_BALANCE, balance_scope=MarketplaceBalanceScope.CHARACTER_INVENTORY, display_name_key="test", min_amount=1)
        listing = MarketplaceListing(seller_account_id=x["seller"], openmu_item_id=x["item"], status=MarketplaceListingStatus.PENDING_ESCROW, item_snapshot_version=1, item_snapshot={}, version=1)
        session.add_all([asset, listing]); session.flush(); session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=asset.id, amount=10)); session.flush()
        create = command(session, MarketplaceCommandType.CREATE_LISTING, x["seller"], listing.id); MarketplacePhysicalExecutor().execute(session, create.id, "pytest")
        character_id = None if character_key is None else (uuid.uuid4() if character_key == "missing" else x[character_key])
        buy = command(session, MarketplaceCommandType.BUY_LISTING, x["buyer"], listing.id); buy.character_id = character_id
        with pytest.raises(Exception, match=error_code):
            MarketplacePhysicalExecutor().execute(session, buy.id, "pytest")
        assert session.execute(text('SELECT "Money" FROM data."ItemStorage" WHERE "Id"=:id'), {"id": x["buyer_inventory"]}).scalar_one() == 1000
        assert session.execute(text('SELECT "Money" FROM data."ItemStorage" WHERE "Id"=:id'), {"id": x["buyer_vault"]}).scalar_one() == 1000
        assert listing.status == MarketplaceListingStatus.ACTIVE


def test_character_inventory_debit_and_credit_use_only_explicit_owned_characters(physical_world):
    x = physical_world
    with Session(engine) as session, session.begin():
        asset = MarketplacePaymentAsset(code=f"PYTEST-{x['seller'].hex[:12]}-CHAR-OK", asset_type=MarketplaceAssetType.NUMERIC_BALANCE, balance_scope=MarketplaceBalanceScope.CHARACTER_INVENTORY, display_name_key="test", min_amount=1)
        listing = MarketplaceListing(seller_account_id=x["seller"], openmu_item_id=x["item"], status=MarketplaceListingStatus.PENDING_ESCROW, item_snapshot_version=1, item_snapshot={}, version=1)
        session.add_all([asset, listing]); session.flush(); session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=asset.id, amount=10)); session.flush()
        create = command(session, MarketplaceCommandType.CREATE_LISTING, x["seller"], listing.id); MarketplacePhysicalExecutor().execute(session, create.id, "pytest")
        buy = command(session, MarketplaceCommandType.BUY_LISTING, x["buyer"], listing.id); buy.character_id = x["buyer_character"]; MarketplacePhysicalExecutor().execute(session, buy.id, "pytest")
        assert session.execute(text('SELECT "Money" FROM data."ItemStorage" WHERE "Id"=:id'), {"id": x["buyer_inventory"]}).scalar_one() == 990
        assert session.execute(text('SELECT "Money" FROM data."ItemStorage" WHERE "Id"=:id'), {"id": x["buyer_vault"]}).scalar_one() == 1000
        proceeds = session.query(MarketplaceProceeds).filter_by(owner_account_id=x["seller"]).one()
        claim = command(session, MarketplaceCommandType.CLAIM_PROCEEDS, x["seller"], proceeds.id); claim.character_id = x["seller_character"]; MarketplacePhysicalExecutor().execute(session, claim.id, "pytest")
        assert session.execute(text('SELECT "Money" FROM data."ItemStorage" WHERE "Id"=:id'), {"id": x["seller_inventory"]}).scalar_one() == 1010
        assert session.execute(text('SELECT "Money" FROM data."ItemStorage" WHERE "Id"=:id'), {"id": x["seller_vault"]}).scalar_one() == 0


@pytest.mark.parametrize("scope", list(MarketplaceBalanceScope))
@pytest.mark.parametrize("available,price,succeeds", [(10, 10, True), (9, 10, False)])
def test_numeric_debit_exact_balance_and_insufficient_are_atomic(physical_world, scope, available, price, succeeds):
    x = physical_world
    target = x["buyer_vault"] if scope == MarketplaceBalanceScope.ACCOUNT_VAULT else x["buyer_inventory"]
    character_id = None if scope == MarketplaceBalanceScope.ACCOUNT_VAULT else x["buyer_character"]
    with Session(engine) as session, session.begin():
        session.execute(text('UPDATE data."ItemStorage" SET "Money"=:money WHERE "Id"=:id'), {"money": available, "id": target})
        asset = MarketplacePaymentAsset(code=f"PYTEST-{x['seller'].hex[:12]}-DEBIT-{scope.value}-{available}", asset_type=MarketplaceAssetType.NUMERIC_BALANCE, balance_scope=scope, display_name_key="test", min_amount=1)
        listing = MarketplaceListing(seller_account_id=x["seller"], openmu_item_id=x["item"], status=MarketplaceListingStatus.PENDING_ESCROW, item_snapshot_version=1, item_snapshot={}, version=1)
        session.add_all([asset, listing]); session.flush(); session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=asset.id, amount=price)); session.flush()
        create = command(session, MarketplaceCommandType.CREATE_LISTING, x["seller"], listing.id); MarketplacePhysicalExecutor().execute(session, create.id, "pytest")
        buy = command(session, MarketplaceCommandType.BUY_LISTING, x["buyer"], listing.id); buy.character_id = character_id
        if succeeds:
            MarketplacePhysicalExecutor().execute(session, buy.id, "pytest")
            assert session.execute(text('SELECT "Money" FROM data."ItemStorage" WHERE "Id"=:id'), {"id": target}).scalar_one() == 0
        else:
            with pytest.raises(Exception, match="MARKETPLACE_INSUFFICIENT_NUMERIC_BALANCE"):
                MarketplacePhysicalExecutor().execute(session, buy.id, "pytest")
            assert session.execute(text('SELECT "Money" FROM data."ItemStorage" WHERE "Id"=:id'), {"id": target}).scalar_one() == available
            assert listing.status == MarketplaceListingStatus.ACTIVE


@pytest.mark.parametrize("scope", list(MarketplaceBalanceScope))
@pytest.mark.parametrize("overflow", [False, True])
def test_numeric_proceeds_credit_enforces_money_cap_without_fallback(physical_world, scope, overflow):
    x = physical_world
    target = x["seller_vault"] if scope == MarketplaceBalanceScope.ACCOUNT_VAULT else x["seller_inventory"]
    character_id = None if scope == MarketplaceBalanceScope.ACCOUNT_VAULT else x["seller_character"]
    limit_column = '"MaximumVaultMoney"' if scope == MarketplaceBalanceScope.ACCOUNT_VAULT else '"MaximumInventoryMoney"'
    with Session(engine) as session, session.begin():
        limit = int(session.execute(text(f'SELECT MIN({limit_column}) FROM config."GameConfiguration"')).scalar_one())
        initial = limit - 9 if overflow else limit - 10
        session.execute(text('UPDATE data."ItemStorage" SET "Money"=:money WHERE "Id"=:id'), {"money": initial, "id": target})
        asset = MarketplacePaymentAsset(code=f"PYTEST-{x['seller'].hex[:12]}-CAP-{scope.value}-{overflow}", asset_type=MarketplaceAssetType.NUMERIC_BALANCE, balance_scope=scope, display_name_key="test", min_amount=1)
        listing = MarketplaceListing(seller_account_id=x["seller"], openmu_item_id=x["item"], status=MarketplaceListingStatus.PENDING_ESCROW, item_snapshot_version=1, item_snapshot={}, version=1)
        session.add_all([asset, listing]); session.flush(); session.add(MarketplaceListingPriceComponent(listing_id=listing.id, payment_asset_id=asset.id, amount=10)); session.flush()
        create = command(session, MarketplaceCommandType.CREATE_LISTING, x["seller"], listing.id); MarketplacePhysicalExecutor().execute(session, create.id, "pytest")
        buy = command(session, MarketplaceCommandType.BUY_LISTING, x["buyer"], listing.id); buy.character_id = x["buyer_character"] if scope == MarketplaceBalanceScope.CHARACTER_INVENTORY else None; MarketplacePhysicalExecutor().execute(session, buy.id, "pytest")
        proceeds = session.query(MarketplaceProceeds).filter_by(owner_account_id=x["seller"]).one()
        claim = command(session, MarketplaceCommandType.CLAIM_PROCEEDS, x["seller"], proceeds.id); claim.character_id = character_id
        MarketplacePhysicalExecutor().execute(session, claim.id, "pytest")
        if overflow:
            assert claim.status == MarketplaceCommandStatus.RETRYABLE_FAILED
            assert claim.last_error_code == "MARKETPLACE_MONEY_CAPACITY"
            assert proceeds.status == MarketplaceClaimStatus.PENDING
            assert session.execute(text('SELECT "Money" FROM data."ItemStorage" WHERE "Id"=:id'), {"id": target}).scalar_one() == initial
        else:
            assert claim.status == MarketplaceCommandStatus.SUCCEEDED
            assert session.execute(text('SELECT "Money" FROM data."ItemStorage" WHERE "Id"=:id'), {"id": target}).scalar_one() == limit


def test_expired_worker_lease_is_reclaimed_and_executes_exactly_once(physical_world):
    x = physical_world
    with Session(engine) as session, session.begin():
        cmd, listing = prepare_physical_command(session, x, MarketplaceCommandType.CREATE_LISTING)
        cmd.status = MarketplaceCommandStatus.PENDING
        cmd.worker_id = None
        cmd.worker_lease_expires_at = None
        cmd.attempts = 0
        command_id = cmd.id

    with Session(engine) as worker_a, worker_a.begin():
        claimed_a = claim_next_command(worker_a, "worker-a", lease=timedelta(minutes=2))
        assert claimed_a is not None and claimed_a.id == command_id
        assert claimed_a.attempts == 1

    with Session(engine) as worker_b, worker_b.begin():
        assert claim_next_command(worker_b, "worker-b") is None

    with Session(engine) as session, session.begin():
        stale = session.get(MarketplaceCommand, command_id)
        stale.worker_lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    with Session(engine) as worker_b, worker_b.begin():
        claimed_b = claim_next_command(worker_b, "worker-b")
        assert claimed_b is not None and claimed_b.id == command_id
        assert claimed_b.attempts == 2
        MarketplacePhysicalExecutor().execute(worker_b, command_id, "worker-b")

    with Session(engine) as session, session.begin():
        completed = session.get(MarketplaceCommand, command_id)
        assert completed.status == MarketplaceCommandStatus.SUCCEEDED
        item_storage = session.execute(text('SELECT "ItemStorageId" FROM data."Item" WHERE "Id"=:id'), {"id": x["item"]}).scalar_one()
        MarketplacePhysicalExecutor().execute(session, command_id, "worker-a")
        assert session.execute(text('SELECT "ItemStorageId" FROM data."Item" WHERE "Id"=:id'), {"id": x["item"]}).scalar_one() == item_storage
        assert completed.attempts == 2


@pytest.mark.parametrize("kind", list(MarketplaceCommandType))
def test_fault_before_command_success_rolls_back_all_physical_and_economic_mutations(physical_world, kind, monkeypatch):
    x = physical_world
    with Session(engine) as session, session.begin():
        cmd, listing = prepare_physical_command(session, x, kind)
        command_id = cmd.id
        listing_id = listing.id
    with Session(engine) as session:
        listing = session.get(MarketplaceListing, listing_id)
        before = economic_snapshot(session, x, listing)
        before_locations = session.execute(text('SELECT count(*) FROM marketplace_item_locations WHERE owner_account_id IN (:seller,:buyer)'), x).scalar_one()

    def fail_before_success(_session, _command):
        raise RuntimeError("PYTEST_FAULT_BEFORE_COMMAND_SUCCESS")

    monkeypatch.setattr(MarketplacePhysicalExecutor, "_succeed", staticmethod(fail_before_success))
    with pytest.raises(RuntimeError, match="PYTEST_FAULT_BEFORE_COMMAND_SUCCESS"):
        with Session(engine) as session, session.begin():
            MarketplacePhysicalExecutor().execute(session, command_id, "pytest")

    with Session(engine) as session:
        listing = session.get(MarketplaceListing, listing_id)
        assert economic_snapshot(session, x, listing) == before
        assert session.get(MarketplaceCommand, command_id).status == MarketplaceCommandStatus.PROCESSING
        assert session.execute(text('SELECT count(*) FROM marketplace_item_locations WHERE owner_account_id IN (:seller,:buyer)'), x).scalar_one() == before_locations
        assert session.execute(text('SELECT count(*) FROM marketplace_audit_events WHERE command_id=:id AND event_type=:event'), {"id": command_id, "event": "MARKETPLACE_COMMAND_SUCCEEDED"}).scalar_one() == 0
