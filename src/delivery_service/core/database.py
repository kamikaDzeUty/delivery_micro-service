from typing import AsyncGenerator

from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from .config import settings

engine = create_async_engine(
    settings.database_url,
    future=True,
    echo=False,
    poolclass=NullPool,
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI-зависимость. Даёт сессию и автоматически её закрывает.
    """
    async with async_session() as session:
        yield session
