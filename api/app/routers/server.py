from fastapi import APIRouter

from app.config import settings
from app.schemas.responses import ServerStatusResponse

router = APIRouter(prefix=settings.api_prefix, tags=["server"])


@router.get("/server/status", response_model=ServerStatusResponse)
def server_status():
    return {
        "status": "development",
        "service": "anastaria-api",
    }
