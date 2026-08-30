from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class ServerStatusResponse(BaseModel):
    status: str
    service: str


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


class RankingsResponse(BaseModel):
    status: str
    items: list[dict]
