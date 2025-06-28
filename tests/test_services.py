import json
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

from src.delivery_service.services.package_service import PackageService
from src.delivery_service.services.rate_service import RateService
from src.delivery_service.services.shipping_service import ShippingService


class TestRateService:
    """Тесты для RateService."""

    @pytest.fixture
    def rate_service(self, mock_http_client, mock_redis):
        """Создание RateService с mock-зависимостями."""
        return RateService(mock_http_client, mock_redis)

    async def test_get_rate_from_cache(self, rate_service, mock_redis):
        """Тест получения курса из кеша."""
        # Настройка мока
        mock_redis.get.return_value = b"95.50"

        rate = await rate_service.get_usd_to_rub_rate()

        assert rate == Decimal("95.50")
        mock_redis.get.assert_called_once_with("usd_to_rub_rate")

    async def test_get_rate_from_api(self, rate_service, mock_http_client, mock_redis):
        """Тест получения курса из API."""
        # Настройка мока
        mock_redis.get.return_value = None

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = json.dumps(
            {"Valute": {"USD": {"Value": 98.75}}}
        )

        mock_http_client.get.return_value.__aenter__.return_value = mock_response

        rate = await rate_service.get_usd_to_rub_rate()

        assert rate == Decimal("98.75")
        mock_redis.set.assert_called_once()

    async def test_get_rate_api_error_fallback(
        self, rate_service, mock_http_client, mock_redis
    ):
        """Тест обработки ошибки API с fallback."""
        # Настройка мока
        mock_redis.get.return_value = None
        mock_http_client.get.side_effect = aiohttp.ClientError("Connection error")

        rate = await rate_service.get_usd_to_rub_rate()

        assert rate == Decimal("100.0")  # Fallback значение

    async def test_clear_cache(self, rate_service, mock_redis):
        """Тест очистки кеша."""
        await rate_service.clear_cache()

        mock_redis.delete.assert_called_once_with("usd_to_rub_rate")

    async def test_get_cache_info(self, rate_service, mock_redis):
        """Тест получения информации о кеше."""
        mock_redis.ttl.return_value = 300
        mock_redis.get.return_value = b"95.50"

        info = await rate_service.get_cache_info()

        assert info["has_cached_value"] is True
        assert info["ttl_seconds"] == 300
        assert info["cached_rate"] == Decimal("95.50")


class TestShippingService:
    """Тесты для ShippingService."""

    @pytest.fixture
    def shipping_service(self):
        """Создание ShippingService с mock rate service."""
        mock_rate_service = AsyncMock()
        mock_rate_service.get_usd_to_rub_rate.return_value = Decimal("95.0")
        return ShippingService(mock_rate_service)

    async def test_calculate_shipping_cost(self, shipping_service):
        """Тест расчета стоимости доставки."""
        weight = Decimal("2.0")
        declared_value = Decimal("500.0")

        cost = await shipping_service.calculate_shipping_cost(weight, declared_value)

        # Базовая стоимость: 2.0 * 100 = 200
        # Стоимость за ценность: 500 * 95 * 0.01 = 475
        # Итого: 200 + 475 = 675
        expected_cost = Decimal("675.00")
        assert cost == expected_cost

    async def test_calculate_shipping_cost_zero_value(self, shipping_service):
        """Тест расчета стоимости для посылки без объявленной стоимости."""
        weight = Decimal("1.0")
        declared_value = Decimal("0.0")

        cost = await shipping_service.calculate_shipping_cost(weight, declared_value)

        # Только базовая стоимость: 1.0 * 100 = 100
        expected_cost = Decimal("100.00")
        assert cost == expected_cost


class TestPackageService:
    """Тесты для PackageService."""

    @pytest.fixture
    def package_service(self):
        """Создание PackageService с mock-зависимостями."""
        mock_repo = AsyncMock()
        mock_shipping = AsyncMock()
        return PackageService(mock_repo, mock_shipping)

    async def test_create_package(
        self, package_service, package_create_data, sample_package
    ):
        """Тест создания посылки."""
        # Настройка мока
        package_service._repo.create.return_value = sample_package

        with patch.object(
            package_service, "_schedule_shipping_calculation"
        ) as mock_schedule:
            result = await package_service.create_package(package_create_data)

        assert result == sample_package
        package_service._repo.create.assert_called_once()
        mock_schedule.assert_called_once_with(sample_package.id)

    async def test_get_package(self, package_service, sample_package):
        """Тест получения посылки."""
        package_service._repo.get.return_value = sample_package

        result = await package_service.get_package(sample_package.id)

        assert result == sample_package
        package_service._repo.get.assert_called_once_with(sample_package.id)

    async def test_get_package_not_found(self, package_service):
        """Тест получения несуществующей посылки."""
        package_service._repo.get.return_value = None

        result = await package_service.get_package("non-existent-id")

        assert result is None

    async def test_list_packages(self, package_service, sample_package):
        """Тест получения списка посылок."""
        package_service._repo.list.return_value = (1, [sample_package])

        total, items = await package_service.list_packages(limit=10, offset=0)

        assert total == 1
        assert len(items) == 1
        assert items[0] == sample_package

    async def test_update_shipping_cost(self, package_service, sample_package):
        """Тест обновления стоимости доставки."""
        calculated_cost = Decimal("750.00")
        updated_package = sample_package
        updated_package.shipping_cost = calculated_cost

        package_service._repo.get.return_value = sample_package
        package_service._shipping.calculate_shipping_cost.return_value = calculated_cost
        package_service._repo.update.return_value = updated_package

        result = await package_service.update_shipping_cost(sample_package.id)

        assert result.shipping_cost == calculated_cost
        package_service._shipping.calculate_shipping_cost.assert_called_once()
        package_service._repo.update.assert_called_once()

    async def test_update_shipping_cost_package_not_found(self, package_service):
        """Тест обновления стоимости для несуществующей посылки."""
        package_service._repo.get.return_value = None

        result = await package_service.update_shipping_cost("non-existent-id")

        assert result is None

    async def test_recalculate_all_pending(self, package_service, sample_package):
        """Тест массового пересчета ожидающих посылок."""
        package_service._repo.list.return_value = (1, [sample_package])

        with patch.object(
            package_service, "_schedule_shipping_calculation"
        ) as mock_schedule:
            tasks_sent = await package_service.recalculate_all_pending()

        assert tasks_sent == 1
        mock_schedule.assert_called_once_with(sample_package.id)
