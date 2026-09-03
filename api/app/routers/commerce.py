from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import SessionLocal
from app.models.commerce import CoinPackage, CurrencyDefinition, ShopProduct
from app.routers.auth import require_game_master
from app.schemas.responses import CoinPackageCreate, CoinPackageItem, CommerceCatalogResponse, CurrencyCreate, CurrencyItem, GameItemCatalogItem, ShopProductCreate, ShopProductItem

router = APIRouter(prefix=settings.api_prefix, tags=["commerce"])

ITEM_CATEGORIES = ["Weapons", "Shields", "Helms", "Armors", "Pants", "Gloves", "Boots", "Wings", "Accessories", "Pets", "Buffs & Consumables", "Jewels & Special", "Miscellaneous"]
LEVEL_EFFECT = (0, 0, 0, 3, 3, 5, 5, 7, 7, 9, 9, 11, 11, 13, 13, 15)


def item_category(group: int, slot: str | None, name: str) -> str:
    slot_categories = {"Helm":"Helms","Armor":"Armors","Pants":"Pants","Gloves":"Gloves","Boots":"Boots","Wings":"Wings","Ring":"Accessories","Pendant":"Accessories","Pet":"Pets"}
    if slot in slot_categories: return slot_categories[slot]
    if group == 6: return "Shields"
    if group in range(0, 6): return "Weapons"
    lowered = name.casefold()
    if group == 14 or any(word in lowered for word in ("potion","elixir","scroll","ale","remedy","food","drink","buff")): return "Buffs & Consumables"
    if group == 13 or any(word in lowered for word in ("jewel","gem","stone","crystal")): return "Jewels & Special"
    return "Miscellaneous"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/commerce/catalog", response_model=CommerceCatalogResponse)
def catalog(db: Session = Depends(get_db)):
    currencies = db.scalars(select(CurrencyDefinition).where(CurrencyDefinition.active.is_(True)).order_by(CurrencyDefinition.sort_order, CurrencyDefinition.id)).all()
    packages = db.scalars(select(CoinPackage).where(CoinPackage.active.is_(True)).order_by(CoinPackage.sort_order, CoinPackage.id)).all()
    products = db.scalars(select(ShopProduct).where(ShopProduct.active.is_(True)).order_by(ShopProduct.sort_order, ShopProduct.id)).all()
    return {"status": "ok", "currencies": currencies, "coin_packages": packages, "products": products}


@router.get("/game/item-categories", response_model=list[str])
def item_categories():
    return ITEM_CATEGORIES


@router.get("/game/items/image")
def game_item_image(group: int, number: int, level: int = 0, variant: str = "normal"):
    if group < 0 or group > 15 or number < 0 or number > 255 or level < 0 or level > 15: raise HTTPException(400,"Invalid item image parameters")
    suffix={"normal":"","excellent":"_e","ancient":"_a"}.get(variant)
    if suffix is None: raise HTTPException(400,"Invalid item image variant")
    effect_level=LEVEL_EFFECT[level]
    base=settings.openmu_server_info_url.rsplit("/api/status",1)[0].rstrip("/")
    candidates = list(dict.fromkeys((
        f"item_{group}_{number}_{effect_level}{suffix}.png",
        f"item_{group}_{number}_{effect_level}.png",
        f"item_{group}_{number}_0{suffix}.png",
        f"item_{group}_{number}_0.png",
    )))
    content = None
    for filename in candidates:
        try:
            with urlopen(f"{base}/_content/MUnique.OpenMU.Web.ItemEditor/img/items/{filename}", timeout=3) as source:
                content = source.read()
                break
        except (HTTPError, URLError, OSError):
            continue
    if content is None:
        raise HTTPException(404, "OpenMU item image not found")
    return Response(content=content,media_type="image/png",headers={"Cache-Control":"public, max-age=86400"})


@router.get("/game/items", response_model=list[GameItemCatalogItem])
def search_game_items(search: str = "", category: str = "", limit: int = 100, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 1000))
    query = text('''
        SELECT i."Id"::text AS id, i."Name" AS name, i."Group" AS "group",
            i."Number" AS number, i."Width" AS width, i."Height" AS height,
            i."MaximumItemLevel" AS maximum_item_level,
            i."Durability" AS durability, i."MaximumSockets" AS maximum_sockets,
            slot."Description" AS slot,
            COALESCE((SELECT array_agg(DISTINCT cc."Name" ORDER BY cc."Name")
                FROM config."ItemDefinitionCharacterClass" link
                JOIN config."CharacterClass" cc ON cc."Id" = link."CharacterClassId"
                WHERE link."ItemDefinitionId" = i."Id"), ARRAY[]::text[]) AS allowed_classes,
            COALESCE((SELECT array_agg(DISTINCT opt."Name" ORDER BY opt."Name")
                FROM config."ItemDefinitionItemOptionDefinition" link
                JOIN config."ItemOptionDefinition" opt ON opt."Id" = link."ItemOptionDefinitionId"
                WHERE link."ItemDefinitionId" = i."Id"), ARRAY[]::text[]) AS available_options,
            COALESCE((SELECT json_agg(json_build_object(
                    'attribute', ad."Designation", 'base_value', power."BaseValue",
                    'aggregate_type', power."AggregateType", 'level_bonuses',
                    COALESCE((SELECT json_agg(json_build_object('level', bonus."Level", 'value', bonus."AdditionalValue") ORDER BY bonus."Level")
                        FROM config."LevelBonus" bonus WHERE bonus."ItemLevelBonusTableId" = power."BonusPerLevelTableId"), '[]'::json)
                ) ORDER BY ad."Designation")
                FROM config."ItemBasePowerUpDefinition" power
                JOIN config."AttributeDefinition" ad ON ad."Id" = power."TargetAttributeId"
                WHERE power."ItemDefinitionId" = i."Id"), '[]'::json) AS base_power_ups
        FROM config."ItemDefinition" i
        LEFT JOIN config."ItemSlotType" slot ON slot."Id" = i."ItemSlotId"
        WHERE (:search = '' OR i."Name" ILIKE :pattern)
        ORDER BY i."Group", i."Number"
        LIMIT :limit
    ''')
    rows = db.execute(query, {"search": search.strip(), "pattern": f"%{search.strip()}%", "limit": 1000}).mappings()
    items=[]
    for row in rows:
        values=dict(row);values["category"]=item_category(values["group"],values["slot"],values["name"])
        if not category or values["category"]==category: items.append(GameItemCatalogItem(**values))
        if len(items)>=limit: break
    return items


@router.post("/commerce/currencies", response_model=CurrencyItem, status_code=status.HTTP_201_CREATED)
def create_currency(payload: CurrencyCreate, db: Session = Depends(get_db), _game_master: dict = Depends(require_game_master)):
    code = payload.code.strip().upper()
    if db.scalar(select(CurrencyDefinition).where(CurrencyDefinition.code == code)):
        raise HTTPException(status_code=409, detail="Currency code already exists")
    item = CurrencyDefinition(**payload.model_dump(exclude={"code"}), code=code)
    db.add(item); db.commit(); db.refresh(item)
    return item


@router.post("/commerce/coin-packages", response_model=CoinPackageItem, status_code=status.HTTP_201_CREATED)
def create_coin_package(payload: CoinPackageCreate, db: Session = Depends(get_db), _game_master: dict = Depends(require_game_master)):
    item = CoinPackage(**payload.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item


@router.post("/commerce/products", response_model=ShopProductItem, status_code=status.HTTP_201_CREATED)
def create_product(payload: ShopProductCreate, db: Session = Depends(get_db), _game_master: dict = Depends(require_game_master)):
    if payload.openmu_item_id:
        exists = db.execute(text('SELECT 1 FROM config."ItemDefinition" WHERE "Id"::text = :item_id'), {"item_id": payload.openmu_item_id}).scalar()
        if not exists:
            raise HTTPException(status_code=404, detail="OpenMU item not found")
    if payload.discount_percent < 0 or payload.discount_percent > 100:
        raise HTTPException(status_code=422, detail="Discount must be between 0 and 100")
    if payload.discount_starts_at and payload.discount_ends_at and payload.discount_ends_at <= payload.discount_starts_at:
        raise HTTPException(status_code=422, detail="Discount end must be after its start")
    item = ShopProduct(**payload.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item


@router.delete("/commerce/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db), _game_master: dict = Depends(require_game_master)):
    item = db.get(ShopProduct, product_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Shop product not found")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
