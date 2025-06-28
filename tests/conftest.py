import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import aiohttp
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from redis.asyncio import Redis

from src.delivery_service.main import app
from src.delivery_service.models.package_type import PackageType
from src.delivery_service.schemas.package import PackageCreate
from src.delivery_service.schemas.package_type import PackageTypeCreate


@pytest.fixture(scope="session")
def event_loop():
    """Создание нового события для всех тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """FastAPI тестовый клиент."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async HTTP клиент."""
    async with AsyncClient(base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_session():
    """Mock сессии."""
    return AsyncMock()


@pytest.fixture
def mock_redis():
    """Mock Redis."""
    redis_mock = AsyncMock(spec=Redis)
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = True
    redis_mock.ttl.return_value = -1
    return redis_mock


@pytest.fixture
def mock_http_client():
    """Mock HTTP client."""
    return AsyncMock(spec=aiohttp.ClientSession)


@pytest.fixture
def sample_package_type():
    """Простой пример типа посылки."""
    return PackageType(id=uuid4(), name="Электроника")


@pytest.fixture
def sample_package(sample_package_type):
    """Простой пример посылки."""
    package = MagicMock()
    package.id = uuid4()
    package.name = "Ноутбук"
    package.weight = Decimal("2.5")
    package.declared_value = Decimal("1000.00")
    package.shipping_cost = None
    package.type_id = sample_package_type.id
    package.type = sample_package_type
    return package


@pytest.fixture
def sample_package_with_cost(sample_package_type):
    """Простой пример посылки с расчетом стоимости доставки."""
    package = MagicMock()
    package.id = uuid4()
    package.name = "Телефон"
    package.weight = Decimal("0.5")
    package.declared_value = Decimal("500.00")
    package.shipping_cost = Decimal("550.00")
    package.type_id = sample_package_type.id
    package.type = sample_package_type
    return package


@pytest.fixture
def package_create_data(sample_package_type):
    """Валидация создания посылки."""
    return PackageCreate(
        name="Тестовая посылка",
        weight=Decimal("1.0"),
        declared_value=Decimal("100.00"),
        type_id=sample_package_type.id,
    )


@pytest.fixture
def package_type_create_data():
    """Валидация создания типа посылки."""
    return PackageTypeCreate(name="Документы")
