from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class ServerStatusResponse(BaseModel):
    status: str
    service: str
    players_online: int | None = None
    version: str | None = None
    season: int | None = None
    episode: int | None = None
    game_servers: int = 0
    checked_at: datetime


class NewsCreate(BaseModel):
    title: str
    summary: str | None = None
    content: str | None = None
    category: str = "UPDATE"
    image_url: str | None = None
    published_at: datetime | None = None


class NewsItem(BaseModel):
    id: int
    title: str
    summary: str | None = None
    content: str | None = None
    category: str
    image_url: str | None = None
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class NewsResponse(BaseModel):
    status: str
    items: list[NewsItem]


class RankingPlayer(BaseModel):
    rank: int
    character_id: str
    name: str
    level: int
    master_level: int = 0
    resets: int = 0
    experience: int
    master_experience: int
    player_kills: int
    character_class: str
    guild_name: str = "—"
    alliance_name: str = "—"
    map_name: str = "—"
    created_at: datetime
    character_status: int
    quest_progress: int = 0
    is_online: bool = False


class GuildRanking(BaseModel):
    rank: int
    name: str
    score: int
    members: int
    alliance: str = "—"


class RankingsResponse(BaseModel):
    status: str
    top_level: list[RankingPlayer]
    top_master: list[RankingPlayer]
    top_killers: list[RankingPlayer]


class GuildsResponse(BaseModel):
    status: str
    guilds: list[GuildRanking]


class CombinedRankingsResponse(BaseModel):
    status: str
    top_level: list[RankingPlayer]
    top_master: list[RankingPlayer]
    top_killers: list[RankingPlayer]
    top_experience: list[RankingPlayer]
    top_resets: list[RankingPlayer]
    top_guilds: list[GuildRanking]
    timestamp: datetime


class EventCreate(BaseModel):
    slug: str
    translations: dict[str, dict[str, str]]
    schedule: str
    timezone: str = "UTC"
    category: str = "WORLD"
    reward_summary: str | None = None
    active: bool = True


class EventItem(EventCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class EventsResponse(BaseModel):
    status: str
    server_time: datetime
    items: list[EventItem]


class SiteSettingUpdate(BaseModel):
    value: dict[str, str | bool | None]


class SiteSettingItem(BaseModel):
    key: str
    value: dict[str, str | bool | None]
    updated_at: datetime


class SiteSettingsResponse(BaseModel):
    status: str
    items: list[SiteSettingItem]


class CurrencyCreate(BaseModel):
    code: str
    name: str
    kind: str
    icon: str | None = None
    purchasable: bool = False
    active: bool = True
    sort_order: int = 0


class CurrencyItem(CurrencyCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class CoinPackageCreate(BaseModel):
    title: str
    description: str | None = None
    currency_code: str
    coin_amount: int
    bonus_amount: int = 0
    price_minor: int
    settlement_currency: str = "EUR"
    image_url: str | None = None
    featured: bool = False
    active: bool = True
    sort_order: int = 0


class CoinPackageItem(CoinPackageCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class ShopProductCreate(BaseModel):
    title: str
    openmu_item_id: str | None = None
    description: str | None = None
    category: str
    currency_code: str
    price_amount: int
    selected_options: dict[str, int | bool | str | list[str]] = Field(default_factory=dict)
    discount_percent: int = 0
    discount_starts_at: datetime | None = None
    discount_ends_at: datetime | None = None
    delivery_code: str | None = None
    image_url: str | None = None
    featured: bool = False
    active: bool = True
    sort_order: int = 0


class ShopProductItem(ShopProductCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class CommerceCatalogResponse(BaseModel):
    status: str
    currencies: list[CurrencyItem]
    coin_packages: list[CoinPackageItem]
    products: list[ShopProductItem]


class GameItemCatalogItem(BaseModel):
    id: str
    name: str
    group: int
    number: int
    width: int
    height: int
    maximum_item_level: int
    durability: int
    maximum_sockets: int
    slot: str | None = None
    category: str
    allowed_classes: list[str] = Field(default_factory=list)
    available_options: list[str] = Field(default_factory=list)
    base_power_ups: list[dict[str, str | int | float | list[dict[str, int | float]]]] = Field(default_factory=list)


