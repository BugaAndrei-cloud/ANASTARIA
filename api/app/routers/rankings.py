from datetime import datetime, timezone
from enum import Enum
import json
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.config import settings
from app.database.session import SessionLocal
from app.schemas.responses import CombinedRankingsResponse, GuildRanking, RankingPlayer

router = APIRouter(prefix=settings.api_prefix, tags=["rankings"])


class RankingType(str, Enum):
    resets = "resets"
    level = "level"
    master = "master"
    experience = "experience"
    killers = "killers"


ORDER_BY = {
    RankingType.resets: "resets DESC, level DESC, experience DESC",
    RankingType.level: "level DESC, experience DESC",
    RankingType.master: "master_level DESC, master_experience DESC",
    RankingType.experience: "experience DESC",
    RankingType.killers: "player_kills DESC, level DESC",
}


def get_online_character_names() -> set[str]:
    """Return live character names without exposing OpenMU's player list."""
    if not settings.openmu_server_info_url:
        return set()
    try:
        with urlopen(settings.openmu_server_info_url, timeout=2) as response:
            payload = json.load(response)
        player_names = payload.get("playersList", [])
        return {str(name).casefold() for name in player_names if name}
    except (OSError, URLError, ValueError, TypeError, json.JSONDecodeError):
        return set()


def get_ranking_players(ranking_type: RankingType, limit: int = 100) -> list[RankingPlayer]:
    order_by = ORDER_BY[ranking_type]
    query = text(f"""
        WITH character_stats AS (
            SELECT s."CharacterId" AS character_id,
                MAX(s."Value") FILTER (WHERE ad."Designation" = 'Level') AS level,
                MAX(s."Value") FILTER (WHERE ad."Designation" = 'Master Level') AS master_level,
                MAX(s."Value") FILTER (WHERE ad."Designation" = 'Resets') AS resets
            FROM data."StatAttribute" s
            JOIN config."AttributeDefinition" ad ON ad."Id" = s."DefinitionId"
            WHERE ad."Designation" IN ('Level', 'Master Level', 'Resets')
            GROUP BY s."CharacterId"
        ), quest_progress AS (
            SELECT "CharacterId" AS character_id, COUNT(*) AS quest_progress
            FROM data."CharacterQuestState"
            WHERE "LastFinishedQuestId" IS NOT NULL
            GROUP BY "CharacterId"
        ), ranked AS (
            SELECT c."Id"::text AS character_id, c."Name" AS name,
                COALESCE(cs.level, 0)::int AS level,
                COALESCE(cs.master_level, 0)::int AS master_level,
                COALESCE(cs.resets, 0)::int AS resets,
                COALESCE(c."Experience", 0) AS experience,
                COALESCE(c."MasterExperience", 0) AS master_experience,
                COALESCE(c."PlayerKillCount", 0) AS player_kills,
                COALESCE(cc."Name", 'Unknown') AS character_class,
                COALESCE(g."Name", '—') AS guild_name,
                COALESCE(a."Name", '—') AS alliance_name,
                COALESCE(m."Name", '—') AS map_name,
                c."CreateDate" AS created_at,
                c."CharacterStatus" AS character_status,
                COALESCE(qp.quest_progress, 0)::int AS quest_progress
            FROM data."Character" c
            LEFT JOIN character_stats cs ON cs.character_id = c."Id"
            LEFT JOIN config."CharacterClass" cc ON cc."Id" = c."CharacterClassId"
            LEFT JOIN config."GameMapDefinition" m ON m."Id" = c."CurrentMapId"
            LEFT JOIN guild."GuildMember" gm ON gm."Id" = c."Id"
            LEFT JOIN guild."Guild" g ON g."Id" = gm."GuildId"
            LEFT JOIN guild."Guild" a ON a."Id" = g."AllianceGuildId"
            LEFT JOIN quest_progress qp ON qp.character_id = c."Id"
        )
        SELECT ROW_NUMBER() OVER (ORDER BY {order_by}) AS rank, ranked.*
        FROM ranked ORDER BY {order_by} LIMIT :limit
    """)
    with SessionLocal() as db:
        rows = db.execute(query, {"limit": limit}).mappings()
        online_names = get_online_character_names()
        return [
            RankingPlayer(**dict(row), is_online=str(row["name"]).casefold() in online_names)
            for row in rows
        ]


def get_guild_rankings(limit: int = 100) -> list[GuildRanking]:
    query = text("""
        SELECT ROW_NUMBER() OVER (ORDER BY g."Score" DESC, g."Name") AS rank,
            g."Name" AS name, COALESCE(g."Score", 0) AS score,
            COUNT(gm."Id") AS members, COALESCE(a."Name", '—') AS alliance
        FROM guild."Guild" g
        LEFT JOIN guild."GuildMember" gm ON gm."GuildId" = g."Id"
        LEFT JOIN guild."Guild" a ON a."Id" = g."AllianceGuildId"
        GROUP BY g."Id", g."Name", g."Score", a."Name"
        ORDER BY g."Score" DESC, g."Name" LIMIT :limit
    """)
    with SessionLocal() as db:
        rows = db.execute(query, {"limit": limit}).mappings()
        return [GuildRanking(**dict(row)) for row in rows]


@router.get("/rankings/all", response_model=CombinedRankingsResponse)
def get_all_rankings(limit: int = Query(default=100, ge=1, le=100)):
    return CombinedRankingsResponse(
        status="ok",
        top_level=get_ranking_players(RankingType.level, limit),
        top_master=get_ranking_players(RankingType.master, limit),
        top_killers=get_ranking_players(RankingType.killers, limit),
        top_experience=get_ranking_players(RankingType.experience, limit),
        top_resets=get_ranking_players(RankingType.resets, limit),
        top_guilds=get_guild_rankings(limit),
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/rankings/guilds/top", response_model=list[GuildRanking])
def get_guilds(limit: int = Query(default=100, ge=1, le=100)):
    return get_guild_rankings(limit)


@router.get("/rankings/{ranking_type}", response_model=list[RankingPlayer])
def get_rankings(ranking_type: RankingType, limit: int = Query(default=100, ge=1, le=100)):
    return get_ranking_players(ranking_type, limit)
