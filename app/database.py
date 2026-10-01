from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=False,
    pool_recycle = 1800,
    connect_args={"statement_cache_size": 0, "timeout": 30},
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI dependency: yields a DB session and always closes it."""
    async with AsyncSessionLocal() as session:
        yield session
