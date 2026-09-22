import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check():
    # reads directly from your .env file
    db_url = os.getenv("DATABASE_URL")
    
    # asyncpg needs slightly different format
    # remove the +asyncpg part for direct asyncpg connection
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        conn = await asyncpg.connect(db_url)
        print("✅ Connected to DB server successfully")

        # check foods table
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM static.foods"
        )
        print(f"static.foods rows: {count} (expect 0)")

        # check all schemas
        schemas = await conn.fetch("""
            SELECT schema_name 
            FROM information_schema.schemata
            WHERE schema_name IN 
            ('core','static','tracking','intelligence')
        """)
        print(f"\nSchemas found: {len(schemas)} (expect 4)")
        for s in schemas:
            print(f"  {s['schema_name']} ✅")

        # check all tables
        tables = await conn.fetch("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE schemaname IN 
            ('core','static','tracking','intelligence')
            ORDER BY schemaname, tablename
        """)
        print(f"\nTables found: {len(tables)} (expect 12)")
        for t in tables:
            print(f"  {t['schemaname']}.{t['tablename']} ✅")

        # check alembic version
        version = await conn.fetchval(
            "SELECT version_num FROM alembic_version"
        )
        print(f"\nAlembic version: {version}")

        await conn.close()

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Check your DATABASE_URL in .env")

asyncio.run(check())