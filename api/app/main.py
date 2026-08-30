from fastapi import FastAPI

from app.routers import news, rankings, server
from app.schemas.responses import (
    HealthResponse,
    NewsResponse,
    RankingsResponse,
    ServerStatusResponse,
)

app = FastAPI(
    title="ANASTARIA API",
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse)
def health():
    return {
        "status": "ok",
        "service": "anastaria-api",
    }


app.include_router(server.router)
app.include_router(news.router)
app.include_router(rankings.router)
