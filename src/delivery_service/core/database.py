from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from .config import settings

engine = create_async_engine(
    str(settings.database_url),
    future=True,
    echo=True,              # При необходимости можно выключить
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session() -> AsyncSession:
    """
    FastAPI-зависимость. Даёт сессию и автоматически её закрывает.
    """
    async with AsyncSessionLocal() as session:
        yield session
