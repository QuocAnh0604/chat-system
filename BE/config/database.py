import asyncio
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from BE.config.settings import DATABASE_URL

database_url = DATABASE_URL
if not database_url:
    raise ValueError("DATABASE_URL must be configured in the environment.")


def _as_async_database_url(url: str) -> str:
    """Use psycopg's async-compatible SQLAlchemy dialect for PostgreSQL URLs."""
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


SQLALCHEMY_DATABASE_URL = _as_async_database_url(database_url)
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
async def check_connection():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Kết nối DB thành công")
        return True
    except Exception as e:
        print(f"❌ Kết nối DB thất bại: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(check_connection())
