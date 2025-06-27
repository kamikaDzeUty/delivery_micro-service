from typing import AsyncGenerator
import aiohttp
from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.delivery_service.core.config import settings
from src.delivery_service.core.database import async_session
from src.delivery_service.repositories.package_repository import PackageRepository
from src.delivery_service.repositories.package_type_repository import PackageTypeRepository
from src.delivery_service.services.rate_service import RateService
from src.delivery_service.services.shipping_service import ShippingService
from src.delivery_service.services.package_service import PackageService


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency для получения сессии БД.
    """
    async with async_session() as session:
        yield session


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """
    FastAPI dependency для получения Redis клиента.
    """
    redis = Redis.from_url(str(settings.redis_url))
    try:
        yield redis
    finally:
        await redis.close()


async def get_http_client() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """
    FastAPI dependency для получения HTTP клиента.
    """
    timeout = aiohttp.ClientTimeout(total=settings.http_timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        yield session


def get_package_repository(session: AsyncSession = Depends(get_session)) -> PackageRepository:
    """
    Dependency для получения репозитория посылок.
    """
    return PackageRepository(session)


def get_package_type_repository(session: AsyncSession = Depends(get_session)) -> PackageTypeRepository:
    """
    Dependency для получения репозитория типов посылок.
    """
    return PackageTypeRepository(session)


def get_rate_service(
    http_client: aiohttp.ClientSession = Depends(get_http_client),
    redis_client: Redis = Depends(get_redis_client),
) -> RateService:
    """
    Dependency для получения сервиса курсов валют.
    """
    return RateService(http_client, redis_client)


def get_shipping_service(
    rate_service: RateService = Depends(get_rate_service),
) -> ShippingService:
    """
    Dependency для получения сервиса расчета доставки.
    """
    return ShippingService(rate_service)


def get_package_service(
    repo: PackageRepository = Depends(get_package_repository),
    shipping_service: ShippingService = Depends(get_shipping_service),
) -> PackageService:
    """
    Dependency для получения сервиса посылок.
    """
    return PackageService(repo, shipping_service) 