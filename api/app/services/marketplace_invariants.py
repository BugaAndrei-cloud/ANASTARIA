"""Read-only PostgreSQL invariant scanner for Marketplace physical ownership."""
from sqlalchemy import text
from sqlalchemy.orm import Session


INVARIANT_QUERIES = {
    "item_location_without_item": '''SELECT count(*) FROM marketplace_item_locations l LEFT JOIN data."Item" i ON i."Id"=l.openmu_item_id WHERE i."Id" IS NULL''',
    "orphan_physical_storage": '''SELECT count(*) FROM marketplace_physical_storages m LEFT JOIN data."ItemStorage" s ON s."Id"=m.openmu_item_storage_id WHERE s."Id" IS NULL''',
    "orphan_physical_storage_registration": '''SELECT count(*) FROM marketplace_physical_storages m WHERE (m.location_type='ESCROW' AND NOT EXISTS (SELECT 1 FROM marketplace_listings l WHERE l.id=m.location_reference_id)) OR (m.location_type='DELIVERY' AND NOT EXISTS (SELECT 1 FROM marketplace_deliveries d WHERE d.id=m.location_reference_id)) OR (m.location_type='PROCEEDS' AND NOT EXISTS (SELECT 1 FROM marketplace_proceeds p WHERE p.id=m.location_reference_id))''',
    "multiple_live_listings_for_item": '''SELECT count(*) FROM (SELECT openmu_item_id FROM marketplace_listings WHERE status IN ('PENDING_ESCROW','ACTIVE','PROCESSING','CANCEL_PENDING') GROUP BY openmu_item_id HAVING count(*) > 1) duplicates''',
    "duplicate_active_deliveries": '''SELECT count(*) FROM (SELECT openmu_item_id FROM marketplace_deliveries WHERE status IN ('PENDING','CLAIMING') GROUP BY openmu_item_id HAVING count(*) > 1) duplicates''',
    "active_listing_item_missing": '''SELECT count(*) FROM marketplace_listings l LEFT JOIN data."Item" i ON i."Id"=l.openmu_item_id WHERE l.status IN ('PENDING_ESCROW','ACTIVE','PROCESSING','CANCEL_PENDING') AND i."Id" IS NULL''',
    "escrow_location_storage_mismatch": '''SELECT count(*) FROM marketplace_item_locations l LEFT JOIN marketplace_physical_storages s ON s.location_type=l.location_type AND s.location_reference_id=l.location_reference_id LEFT JOIN data."Item" i ON i."Id"=l.openmu_item_id WHERE l.location_type='ESCROW' AND (s.id IS NULL OR i."ItemStorageId" IS DISTINCT FROM s.openmu_item_storage_id)''',
    "delivery_owner_mismatch": '''SELECT count(*) FROM marketplace_item_locations l LEFT JOIN marketplace_deliveries d ON d.id=l.location_reference_id AND d.openmu_item_id=l.openmu_item_id AND d.owner_account_id=l.owner_account_id AND d.status IN ('PENDING','CLAIMING') WHERE l.location_type='DELIVERY' AND d.id IS NULL''',
    "proceeds_owner_mismatch": '''SELECT count(*) FROM marketplace_item_locations l LEFT JOIN marketplace_proceeds_components c ON c.openmu_item_id=l.openmu_item_id LEFT JOIN marketplace_proceeds p ON p.id=c.proceeds_id AND p.id=l.location_reference_id AND p.owner_account_id=l.owner_account_id AND p.status IN ('PENDING','CLAIMING') WHERE l.location_type='PROCEEDS' AND p.id IS NULL''',
    "market_item_attached_to_player": '''SELECT count(*) FROM marketplace_item_locations l JOIN data."Item" i ON i."Id"=l.openmu_item_id WHERE EXISTS (SELECT 1 FROM data."Account" a WHERE a."VaultId"=i."ItemStorageId" UNION ALL SELECT 1 FROM data."Character" c WHERE c."InventoryId"=i."ItemStorageId")''',
    "claimed_delivery_still_market_owned": '''SELECT count(*) FROM marketplace_deliveries d JOIN marketplace_item_locations l ON l.openmu_item_id=d.openmu_item_id WHERE d.status='CLAIMED' AND l.location_type='DELIVERY' ''',
    "claimed_proceeds_still_market_owned": '''SELECT count(*) FROM marketplace_proceeds p JOIN marketplace_proceeds_components c ON c.proceeds_id=p.id JOIN marketplace_item_locations l ON l.openmu_item_id=c.openmu_item_id WHERE p.status='CLAIMED' AND l.location_type='PROCEEDS' ''',
    "duplicate_transaction_for_listing": "SELECT count(*) FROM (SELECT listing_id FROM marketplace_transactions GROUP BY listing_id HAVING count(*) > 1) duplicates",
    "negative_market_owner_money": '''SELECT count(*) FROM data."ItemStorage" s JOIN marketplace_physical_storages m ON m.openmu_item_storage_id=s."Id" WHERE s."Money" < 0''',
    "active_listing_without_escrow": '''SELECT count(*) FROM marketplace_listings l LEFT JOIN marketplace_item_locations loc ON loc.openmu_item_id=l.openmu_item_id AND loc.location_type='ESCROW' AND loc.location_reference_id=l.id WHERE l.status='ACTIVE' AND loc.openmu_item_id IS NULL''',
    "pending_delivery_without_location": '''SELECT count(*) FROM marketplace_deliveries d LEFT JOIN marketplace_item_locations loc ON loc.openmu_item_id=d.openmu_item_id AND loc.location_type='DELIVERY' AND loc.location_reference_id=d.id WHERE d.status IN ('PENDING','CLAIMING') AND loc.openmu_item_id IS NULL''',
    "pending_physical_proceeds_without_location": '''SELECT count(*) FROM marketplace_proceeds p JOIN marketplace_proceeds_components c ON c.proceeds_id=p.id AND c.openmu_item_id IS NOT NULL LEFT JOIN marketplace_item_locations loc ON loc.openmu_item_id=c.openmu_item_id AND loc.location_type='PROCEEDS' AND loc.location_reference_id=p.id WHERE p.status IN ('PENDING','CLAIMING') AND loc.openmu_item_id IS NULL''',
    "invalid_location_fencing_token": '''SELECT count(*) FROM marketplace_item_locations loc LEFT JOIN marketplace_account_fences f ON f.account_id=loc.owner_account_id WHERE loc.owner_account_id IS NOT NULL AND (f.account_id IS NULL OR loc.fencing_token > f.fencing_token)''',
    "orphan_command_aggregate": '''SELECT count(*) FROM marketplace_commands c WHERE (c.aggregate_type='listing' AND NOT EXISTS (SELECT 1 FROM marketplace_listings l WHERE l.id=c.aggregate_id)) OR (c.aggregate_type='delivery' AND NOT EXISTS (SELECT 1 FROM marketplace_deliveries d WHERE d.id=c.aggregate_id)) OR (c.aggregate_type='proceeds' AND NOT EXISTS (SELECT 1 FROM marketplace_proceeds p WHERE p.id=c.aggregate_id))''',
    "orphan_idempotency_command": '''SELECT count(*) FROM marketplace_idempotency i LEFT JOIN marketplace_commands c ON c.id=i.command_id WHERE i.command_id IS NOT NULL AND c.id IS NULL''',
}


def scan_marketplace_invariants(session: Session) -> dict[str, int]:
    if session.bind is None or session.bind.dialect.name != "postgresql":
        raise RuntimeError("Marketplace invariant scanning requires PostgreSQL")
    return {name: int(session.execute(text(sql)).scalar_one()) for name, sql in INVARIANT_QUERIES.items()}
