import sys
import asyncio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import inspect

from BE.config.database import DATABASE_URL, engine
print("--- THONG TIN KET NOI ---")
print("DATABASE_URL:", DATABASE_URL)

async def check():
    async with engine.connect() as conn:
        tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
        print("--- DANH SACH BANG TRONG DB NAY ---")
        print(tables)

if __name__ == "__main__":
    asyncio.run(check())