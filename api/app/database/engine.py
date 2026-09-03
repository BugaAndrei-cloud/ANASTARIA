from sqlalchemy import create_engine

from app.config import settings


if not settings.database_url:
    raise RuntimeError("DATABASE_URL is not configured")


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)


