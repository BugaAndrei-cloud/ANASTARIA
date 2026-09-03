from sqlalchemy import create_engine, inspect, text

from app.config import settings


if not settings.database_url:
    raise RuntimeError("DATABASE_URL is not configured")

engine = create_engine(settings.database_url)
inspector = inspect(engine)

print("=== CHARACTER COLUMNS ===")
for col in inspector.get_columns('Character', schema='data'):
    print(f"{col['name']}: {col['type']}")

print("\n=== GUILD COLUMNS ===")
try:
    for col in inspector.get_columns('Guild', schema='data'):
        print(f"{col['name']}: {col['type']}")
except:
    print("Guild table not found in data schema")

print("\n=== STAT_ATTRIBUTE COLUMNS ===")
for col in inspector.get_columns('StatAttribute', schema='data'):
    print(f"{col['name']}: {col['type']}")

print("\n=== LEVEL-RELATED STAT DEFINITIONS ===")
with engine.connect() as connection:
    rows = connection.execute(text('''
        SELECT sad."Id", ad."Designation", ad."Description"
        FROM config."StatAttributeDefinition" sad
        JOIN config."AttributeDefinition" ad ON ad."Id" = sad."AttributeId"
        WHERE ad."Designation" ILIKE '%level%'
           OR ad."Designation" ILIKE '%reset%'
           OR ad."Description" ILIKE '%level%'
           OR ad."Description" ILIKE '%reset%'
        ORDER BY ad."Designation"
    '''))
    for row in rows:
        print(f"{row[0]}: {row[1]} — {row[2]}")

    print("\n=== STORED STAT DEFINITION SAMPLE ===")
    rows = connection.execute(text('''
        SELECT s."DefinitionId", COUNT(*), MIN(s."Value"), MAX(s."Value"),
               ad."Designation"
        FROM data."StatAttribute" s
        LEFT JOIN config."AttributeDefinition" ad ON ad."Id" = s."DefinitionId"
        GROUP BY s."DefinitionId", ad."Designation"
        ORDER BY COUNT(*) DESC
        LIMIT 20
    '''))
    for row in rows:
        print(tuple(row))

print("\n=== ACHIEVEMENT-RELATED TABLES ===")
for schema in inspector.get_schema_names():
    for table in inspector.get_table_names(schema=schema):
        lowered = table.lower()
        if any(term in lowered for term in ("achievement", "quest", "mission", "event")):
            print(f"{schema}.{table}")

for schema, table in (
    ("config", "AttributeDefinition"),
    ("config", "QuestDefinition"),
    ("data", "CharacterQuestState"),
    ("config", "GameMapDefinition"),
):
    print(f"\n=== {schema}.{table} COLUMNS ===")
    for column in inspector.get_columns(table, schema=schema):
        print(f"{column['name']}: {column['type']}")

print("\n=== CHARACTER_SKILL COLUMNS (if exists) ===")
try:
    for col in inspector.get_columns('CharacterSkill', schema='data'):
        print(f"{col['name']}: {col['type']}")
except:
    print("CharacterSkill table not found")


