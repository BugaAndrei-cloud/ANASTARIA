from sqlalchemy import create_engine, inspect

engine = create_engine("postgresql://postgres:admin@127.0.0.1:5432/openmu")
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

print("\n=== CHARACTER_SKILL COLUMNS (if exists) ===")
try:
    for col in inspector.get_columns('CharacterSkill', schema='data'):
        print(f"{col['name']}: {col['type']}")
except:
    print("CharacterSkill table not found")
