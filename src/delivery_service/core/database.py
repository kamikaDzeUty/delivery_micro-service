from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from .config import settings

engine = create_async_engine(
    str(settings.database_url),
    echo=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI-зависимость. Даёт сессию и автоматически её закрывает.
    """
    async with AsyncSessionLocal() as session:
        yield session
