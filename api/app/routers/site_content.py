import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import SessionLocal
from app.models.site_content import GameEvent, SiteSetting
from app.routers.auth import require_game_master
from app.schemas.responses import EventCreate, EventItem, EventsResponse, SiteSettingItem, SiteSettingsResponse, SiteSettingUpdate

router = APIRouter(prefix=settings.api_prefix, tags=["site-content"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/events", response_model=EventsResponse)
def list_events(db: Session = Depends(get_db)):
    items = db.execute(select(GameEvent).where(GameEvent.active.is_(True)).order_by(GameEvent.id)).scalars().all()
    now = datetime.now(timezone.utc)
    definitions = [
        ("95e68c14-ad87-4b3c-af46-45b8f1c3bc2a", "blood-castle", "Blood Castle", "Every two hours", "MINI GAME", range(0, 24, 2)),
        ("3ad96a70-ed24-4979-80b8-169e461e548f", "chaos-castle", "Chaos Castle", "Every hour", "MINI GAME", range(24)),
        ("61c61a58-211e-4d6a-9ea1-d25e0c4a47c5", "devil-square", "Devil Square", "Every four hours", "MINI GAME", range(0, 24, 4)),
        ("06d18a9e-2919-4c17-9dbc-6e4f7756495c", "golden-invasion", "Golden Invasion", "Golden monsters invade Lorencia, Noria, Devias, Atlans and Tarkan.", "INVASION", range(0, 24, 4)),
        ("548a76cc-242c-441c-bc9d-6c22745a2d72", "red-dragon-invasion", "Red Dragon Invasion", "Red Dragons invade Lorencia, Noria and Devias.", "INVASION", range(2, 24, 6)),
        ("4b5d0f55-5b26-4447-b9c0-c272e5d0a141", "white-wizard-invasion", "White Wizard Invasion", "Defeat the White Wizard and his corps.", "INVASION", range(12, 24, 2)),
        ("6542e452-9780-45b8-85ae-4036422e9a6e", "happy-hour", "Happy Hour", "Temporary server bonuses for every player.", "WORLD", range(0, 24, 6)),
    ]
    configs = {str(row.TypeId).lower(): row for row in db.execute(text('SELECT "TypeId", "IsActive", "CustomConfiguration" FROM config."PlugInConfiguration" WHERE "TypeId"::text = ANY(:ids)'), {"ids": [item[0] for item in definitions]}).all()}
    live = []
    for index, (type_id, slug, name, description, category, default_hours) in enumerate(definitions, 1):
        config = configs.get(type_id)
        if config is not None and not config.IsActive:
            continue
        times = [f"{hour:02d}:{5 if slug == 'happy-hour' else 0:02d}" for hour in default_hours]
        if config is not None and config.CustomConfiguration:
            try:
                values = json.loads(config.CustomConfiguration).get("Timetable", {}).get("$values", [])
                times = [str(value)[:5] for value in values] or times
            except (ValueError, TypeError, AttributeError):
                pass
        live.append({"id": -index, "slug": slug, "translations": {"en": {"title": name, "description": description}}, "schedule": ", ".join(times), "timezone": "UTC", "category": category, "reward_summary": None, "active": True, "created_at": now, "updated_at": now})
    return {"status": "ok", "server_time": now, "items": live + list(items)}


@router.post("/events", response_model=EventItem, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: Session = Depends(get_db), _game_master: dict = Depends(require_game_master)):
    if db.scalar(select(GameEvent).where(GameEvent.slug == payload.slug)):
        raise HTTPException(status_code=409, detail="Event slug already exists")
    item = GameEvent(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/events/{event_id}", response_model=EventItem)
def update_event(event_id: int, payload: EventCreate, db: Session = Depends(get_db), _game_master: dict = Depends(require_game_master)):
    item = db.get(GameEvent, event_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Event not found")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.get("/site-settings", response_model=SiteSettingsResponse)
def list_site_settings(db: Session = Depends(get_db)):
    items = db.execute(select(SiteSetting).order_by(SiteSetting.key)).scalars().all()
    return {"status": "ok", "items": items}


@router.put("/site-settings/{setting_key}", response_model=SiteSettingItem)
def update_site_setting(setting_key: str, payload: SiteSettingUpdate, db: Session = Depends(get_db), _game_master: dict = Depends(require_game_master)):
    item = db.scalar(select(SiteSetting).where(SiteSetting.key == setting_key))
    if item is None:
        item = SiteSetting(key=setting_key, value=payload.value)
        db.add(item)
    else:
        item.value = payload.value
    db.commit()
    db.refresh(item)
    return item
