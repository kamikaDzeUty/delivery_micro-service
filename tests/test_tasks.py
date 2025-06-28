from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.delivery_service.tasks.recalc import (
    _recalc_shipping_cost_async,
    bulk_recalc_shipping_cost,
    recalc_shipping_cost,
)


class TestCeleryTasks:
    """Тесты для задач Celery."""

    def test_recalc_shipping_cost_success(self):
        """Тест успешного пересчета стоимости доставки через Celery."""
        package_id = str(uuid4())

        # Создаем mock для результата
        mock_package = MagicMock()
        mock_package.shipping_cost = Decimal("675.00")

        with patch("src.delivery_service.tasks.recalc.asyncio.run") as mock_asyncio:
            mock_asyncio.return_value = mock_package

            # Создаем mock для self (Celery task instance)
            mock_self = MagicMock()

            result = recalc_shipping_cost(mock_self, package_id)

            assert result["status"] == "success"
            assert result["package_id"] == package_id
            assert result["shipping_cost"] == "675.00"

    def test_recalc_shipping_cost_package_not_found(self):
        """Тест пересчета стоимости для несуществующей посылки."""
        package_id = str(uuid4())

        with patch("src.delivery_service.tasks.recalc.asyncio.run") as mock_asyncio:
            mock_asyncio.return_value = None

            mock_self = MagicMock()

            result = recalc_shipping_cost(mock_self, package_id)

            assert result["status"] == "not_found"
            assert result["package_id"] == package_id

    def test_recalc_shipping_cost_invalid_uuid(self):
        """Тест пересчета стоимости с невалидным UUID."""
        invalid_package_id = "invalid-uuid"

        mock_self = MagicMock()
        mock_self.retry = MagicMock(side_effect=Exception("Retry called"))

        with pytest.raises(Exception):
            recalc_shipping_cost(mock_self, invalid_package_id)

    def test_bulk_recalc_shipping_cost_success(self):
        """Тест массового пересчета стоимости доставки."""
        package_ids = [str(uuid4()), str(uuid4()), str(uuid4())]

        with patch(
            "src.delivery_service.tasks.recalc.recalc_shipping_cost.delay"
        ) as mock_delay:
            mock_self = MagicMock()

            result = bulk_recalc_shipping_cost(mock_self, package_ids)

            assert result["tasks_scheduled"] == 3
            assert len(result["errors"]) == 0
            assert mock_delay.call_count == 3

    @pytest.mark.asyncio
    async def test_recalc_shipping_cost_async_success(self, sample_package):
        """Тест асинхронной функции пересчета стоимости."""
        package_id = sample_package.id

        # Мокаем все внешние зависимости
        with patch("src.delivery_service.tasks.recalc.async_session") as mock_session:
            mock_session.return_value.__aenter__.return_value = AsyncMock()

            with patch(
                "src.delivery_service.tasks.recalc.PackageRepository"
            ) as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo.get.return_value = sample_package

                # Создаем новый объект для результата
                updated_package = MagicMock()
                updated_package.shipping_cost = Decimal("500.00")
                mock_repo.update.return_value = updated_package

                mock_repo_class.return_value = mock_repo

                with (
                    patch("src.delivery_service.tasks.recalc.aiohttp.ClientSession"),
                    patch("src.delivery_service.tasks.recalc.Redis"),
                    patch("src.delivery_service.tasks.recalc.RateService"),
                    patch(
                        "src.delivery_service.tasks.recalc.ShippingService"
                    ) as mock_shipping_class,
                ):
                    mock_shipping = AsyncMock()
                    mock_shipping.calculate_shipping_cost.return_value = Decimal(
                        "500.00"
                    )
                    mock_shipping_class.return_value = mock_shipping

                    result = await _recalc_shipping_cost_async(package_id)

                    assert result is not None
                    assert result.shipping_cost == Decimal("500.00")

    @pytest.mark.asyncio
    async def test_recalc_shipping_cost_async_not_found(self):
        """Тест асинхронной функции для несуществующей посылки."""
        package_id = uuid4()

        with patch("src.delivery_service.tasks.recalc.async_session") as mock_session:
            mock_session.return_value.__aenter__.return_value = AsyncMock()

            with patch(
                "src.delivery_service.tasks.recalc.PackageRepository"
            ) as mock_repo_class:
                mock_repo = AsyncMock()
                mock_repo.get.return_value = None
                mock_repo_class.return_value = mock_repo

                result = await _recalc_shipping_cost_async(package_id)

                assert result is None
