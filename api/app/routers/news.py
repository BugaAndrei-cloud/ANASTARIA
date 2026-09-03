from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import SessionLocal
from app.models.news import News
from app.routers.auth import require_game_master
from app.schemas.responses import NewsCreate, NewsItem, NewsResponse

router = APIRouter(
    prefix=settings.api_prefix,
    tags=["news"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/news", response_model=NewsResponse)
def news(db: Session = Depends(get_db)):
    result = db.execute(
        select(News).order_by(
            News.published_at.desc().nullslast(),
            News.id.desc(),
        )
    )

    items = result.scalars().all()

    return {
        "status": "ok",
        "items": items,
    }


@router.get("/news/{news_id}", response_model=NewsItem)
def get_news(
    news_id: int,
    db: Session = Depends(get_db),
):
    item = db.get(News, news_id)

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News article not found",
        )

    return item


@router.post(
    "/news",
    response_model=NewsItem,
    status_code=status.HTTP_201_CREATED,
)
def create_news(
    payload: NewsCreate,
    db: Session = Depends(get_db),
    _game_master: dict = Depends(require_game_master),
):
    item = News(
        title=payload.title,
        summary=payload.summary,
        content=payload.content,
        category=payload.category,
        image_url=payload.image_url,
        published_at=payload.published_at,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


