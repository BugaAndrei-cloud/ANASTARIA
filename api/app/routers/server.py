import json
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import APIRouter

from app.config import settings
from app.schemas.responses import ServerStatusResponse

router = APIRouter(prefix=settings.api_prefix, tags=["server"])


@router.get("/server/status", response_model=ServerStatusResponse)
def server_status():
    checked_at = datetime.now(timezone.utc)
    if not settings.openmu_server_info_url:
        return {"status": "unconfigured", "service": "openmu", "checked_at": checked_at}
    try:
        with urlopen(settings.openmu_server_info_url, timeout=2) as response:
            payload = json.load(response)

        # The OpenMU all-in-one host exposes /api/status, while the standalone
        # ConnectServer host exposes /ServerInfo. Support both official shapes.
        if "players" in payload:
            state = str(payload.get("state", "offline")).lower()
            return {
                "status": "online" if state == "online" else "offline",
                "service": "openmu",
                "players_online": int(payload.get("players", 0)),
                "game_servers": len(payload.get("playersList", [])),
                "checked_at": checked_at,
            }

        game_servers = payload.get("gameServers", payload.get("GameServers", []))
        players = sum(int(item.get("currentConnections", item.get("CurrentConnections", 0))) for item in game_servers)
        return {
            "status": "online" if game_servers else "offline", "service": "openmu",
            "players_online": players, "version": payload.get("version", payload.get("Version")),
            "season": payload.get("season", payload.get("Season")), "episode": payload.get("episode", payload.get("Episode")),
            "game_servers": len(game_servers), "checked_at": checked_at,
        }
    except (OSError, URLError, ValueError, json.JSONDecodeError):
        return {"status": "offline", "service": "openmu", "checked_at": checked_at}
