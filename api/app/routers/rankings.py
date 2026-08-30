from fastapi import APIRouter

from app.config import settings
from app.schemas.responses import RankingsResponse

router = APIRouter(prefix=settings.api_prefix, tags=["rankings"])


@router.get("/rankings", response_model=RankingsResponse)
def rankings():
    return {
        "status": "development",
        "items": [],
    }
