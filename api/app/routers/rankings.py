from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.database.session import SessionLocal
from app.schemas.responses import RankingsResponse, RankingPlayer

router = APIRouter(prefix=settings.api_prefix, tags=["rankings"])

LEVEL_DEFINITION_ID = "560931ad-0901-4342-b7f4-fd2e2fcc0563"


@router.get("/rankings", response_model=RankingsResponse)
def rankings():
    with SessionLocal() as db:
        # Top Level
        top_level_rows = db.execute(
            text("""
                SELECT
                    c."Name" AS name,
                    s."Value" AS level,
                    c."Experience" AS experience,
                    c."MasterExperience" AS master_experience,
                    c."PlayerKillCount" AS player_kills,
                    cc."Name" AS character_class
                FROM data."Character" c
                JOIN data."StatAttribute" s
                    ON s."CharacterId" = c."Id"
                JOIN config."CharacterClass" cc
                    ON cc."Id" = c."CharacterClassId"
                WHERE s."DefinitionId" = :level_definition_id
                ORDER BY
                    s."Value" DESC,
                    c."MasterExperience" DESC,
                    c."Experience" DESC,
                    c."Name" ASC
                LIMIT 10
            """),
            {"level_definition_id": LEVEL_DEFINITION_ID},
        )
        top_level = [
            {**dict(row), "rank": idx + 1} 
            for idx, row in enumerate(top_level_rows.mappings())
        ]

        # Top Master
        top_master_rows = db.execute(
            text("""
                SELECT
                    c."Name" AS name,
                    s."Value" AS level,
                    c."Experience" AS experience,
                    c."MasterExperience" AS master_experience,
                    c."PlayerKillCount" AS player_kills,
                    cc."Name" AS character_class
                FROM data."Character" c
                JOIN data."StatAttribute" s
                    ON s."CharacterId" = c."Id"
                JOIN config."CharacterClass" cc
                    ON cc."Id" = c."CharacterClassId"
                WHERE s."DefinitionId" = :level_definition_id
                ORDER BY
                    c."MasterExperience" DESC,
                    s."Value" DESC,
                    c."Experience" DESC,
                    c."Name" ASC
                LIMIT 10
            """),
            {"level_definition_id": LEVEL_DEFINITION_ID},
        )
        top_master = [
            {**dict(row), "rank": idx + 1} 
            for idx, row in enumerate(top_master_rows.mappings())
        ]

        # Top Killers
        top_killers_rows = db.execute(
            text("""
                SELECT
                    c."Name" AS name,
                    s."Value" AS level,
                    c."Experience" AS experience,
                    c."MasterExperience" AS master_experience,
                    c."PlayerKillCount" AS player_kills,
                    cc."Name" AS character_class
                FROM data."Character" c
                JOIN data."StatAttribute" s
                    ON s."CharacterId" = c."Id"
                JOIN config."CharacterClass" cc
                    ON cc."Id" = c."CharacterClassId"
                WHERE s."DefinitionId" = :level_definition_id
                    AND c."PlayerKillCount" > 0
                ORDER BY
                    c."PlayerKillCount" DESC,
                    s."Value" DESC,
                    c."MasterExperience" DESC,
                    c."Name" ASC
                LIMIT 10
            """),
            {"level_definition_id": LEVEL_DEFINITION_ID},
        )
        top_killers = [
            {**dict(row), "rank": idx + 1} 
            for idx, row in enumerate(top_killers_rows.mappings())
        ]

    return {
        "status": "ok",
        "top_level": top_level,
        "top_master": top_master,
        "top_killers": top_killers,
    }