"""harden marketplace physical storage authority

Revision ID: e926c53df40a
Revises: d815a42be3fc
"""
from collections.abc import Sequence
from alembic import op

revision: str = "e926c53df40a"
down_revision: str | None = "d815a42be3fc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('''
        CREATE FUNCTION marketplace_guard_physical_storage_metadata() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
          IF EXISTS (SELECT 1 FROM data."Item" WHERE "ItemStorageId" = OLD.openmu_item_storage_id) THEN
            RAISE EXCEPTION 'MARKETPLACE_STORAGE_STILL_OWNS_ITEMS' USING ERRCODE = '23514';
          END IF;
          RETURN OLD;
        END $$;
        CREATE TRIGGER trg_marketplace_guard_physical_storage_metadata
        BEFORE DELETE OR UPDATE OF openmu_item_storage_id ON marketplace_physical_storages
        FOR EACH ROW EXECUTE FUNCTION marketplace_guard_physical_storage_metadata();

        CREATE FUNCTION marketplace_guard_item_location_metadata() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM data."Item" i
            JOIN marketplace_physical_storages s ON s.openmu_item_storage_id = i."ItemStorageId"
            WHERE i."Id" = OLD.openmu_item_id
          ) THEN
            RAISE EXCEPTION 'MARKETPLACE_ITEM_STILL_MARKETPLACE_OWNED' USING ERRCODE = '23514';
          END IF;
          RETURN OLD;
        END $$;
        CREATE TRIGGER trg_marketplace_guard_item_location_metadata
        BEFORE DELETE ON marketplace_item_locations
        FOR EACH ROW EXECUTE FUNCTION marketplace_guard_item_location_metadata();
    ''')


def downgrade() -> None:
    op.execute('''
        DROP TRIGGER IF EXISTS trg_marketplace_guard_item_location_metadata ON marketplace_item_locations;
        DROP FUNCTION IF EXISTS marketplace_guard_item_location_metadata();
        DROP TRIGGER IF EXISTS trg_marketplace_guard_physical_storage_metadata ON marketplace_physical_storages;
        DROP FUNCTION IF EXISTS marketplace_guard_physical_storage_metadata();
    ''')
