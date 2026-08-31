from sqlalchemy import create_engine, inspect

engine = create_engine("postgresql://postgres:admin@127.0.0.1:5432/openmu")
inspector = inspect(engine)

# Verific toate schema-urile
schemas = inspector.get_schema_names()
print("Available schemas:", schemas)

# Caut Guild în fiecare schema
for schema in schemas:
    print(f"\n=== Schema: {schema} ===")
    try:
        tables = inspector.get_table_names(schema=schema)
        guild_tables = [t for t in tables if "guild" in t.lower()]
        if guild_tables:
            print(f"Guild tables found: {guild_tables}")
            for table in guild_tables:
                print(f"\n  Columns in {table}:")
                for col in inspector.get_columns(table, schema=schema):
                    print(f"    {col['name']}: {col['type']}")
    except:
        pass
