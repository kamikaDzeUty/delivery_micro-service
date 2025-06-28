from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.delivery_service.main import app


class TestPackagesAPI:
    """Тесты для API посылок."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    def test_create_package_success(self, client, sample_package_type):
        """Тест успешного создания посылки."""

        with patch(
            "src.delivery_service.core.dependencies.get_package_service"
        ) as mock_service:
            # Создаем mock для возвращаемой посылки
            created_package = type(
                "Package",
                (),
                {
                    "id": uuid4(),
                    "name": "Тестовая посылка",
                    "weight": Decimal("1.5"),
                    "declared_value": Decimal("100.00"),
                    "shipping_cost": None,
                    "type_id": sample_package_type.id,
                    "type": sample_package_type,
                },
            )()

            mock_service_instance = AsyncMock()
            mock_service_instance.create_package.return_value = created_package
            mock_service.return_value = mock_service_instance

            payload = {
                "name": "Тестовая посылка",
                "weight": "1.5",
                "declared_value": "100.00",
                "type_id": str(sample_package_type.id),
            }

            response = client.post("/packages/", json=payload)

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["name"] == "Тестовая посылка"
            assert data["weight"] == "1.5"

    def test_create_package_invalid_data(self, client):
        """Тест создания посылки с невалидными данными."""
        payload = {
            "name": "",  # Пустое имя
            "weight": "-1.0",  # Отрицательный вес
            "declared_value": "100.00",
            "type_id": str(uuid4()),
        }

        response = client.post("/packages/", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_package_success(self, client, sample_package_with_cost):
        """Тест успешного получения посылки."""

        with patch(
            "src.delivery_service.core.dependencies.get_package_service"
        ) as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_package.return_value = sample_package_with_cost
            mock_service.return_value = mock_service_instance

            response = client.get(f"/packages/{sample_package_with_cost.id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == str(sample_package_with_cost.id)
            assert data["name"] == sample_package_with_cost.name

    def test_get_package_not_found(self, client):
        """Тест получения несуществующей посылки."""

        with patch(
            "src.delivery_service.core.dependencies.get_package_service"
        ) as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_package.return_value = None
            mock_service.return_value = mock_service_instance

            package_id = uuid4()
            response = client.get(f"/packages/{package_id}")

            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_packages_success(self, client, sample_package_with_cost):
        """Тест получения списка посылок."""

        with patch(
            "src.delivery_service.core.dependencies.get_package_service"
        ) as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.list_packages.return_value = (
                1,
                [sample_package_with_cost],
            )
            mock_service.return_value = mock_service_instance

            response = client.get("/packages/")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total"] == 1
            assert len(data["items"]) == 1
            assert data["items"][0]["id"] == str(sample_package_with_cost.id)

    def test_list_packages_with_filters(self, client):
        """Тест получения списка посылок с фильтрами."""

        with patch(
            "src.delivery_service.core.dependencies.get_package_service"
        ) as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.list_packages.return_value = (0, [])
            mock_service.return_value = mock_service_instance

            type_id = uuid4()
            response = client.get(
                f"/packages/?type_id={type_id}&calculated=true&limit=50&offset=10"
            )

            assert response.status_code == status.HTTP_200_OK
            # Проверяем, что сервис был вызван с правильными параметрами
            mock_service_instance.list_packages.assert_called_once_with(
                type_id=type_id, has_cost=True, limit=50, offset=10
            )

    def test_calculate_shipping_cost_success(self, client, sample_package_with_cost):
        """Тест успешного расчета стоимости доставки."""

        with patch(
            "src.delivery_service.core.dependencies.get_package_service"
        ) as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.update_shipping_cost.return_value = (
                sample_package_with_cost
            )
            mock_service.return_value = mock_service_instance

            response = client.post(f"/packages/{sample_package_with_cost.id}/calculate")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["shipping_cost"] == str(sample_package_with_cost.shipping_cost)

    def test_calculate_shipping_cost_not_found(self, client):
        """Тест расчета стоимости для несуществующей посылки."""

        with patch(
            "src.delivery_service.core.dependencies.get_package_service"
        ) as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.update_shipping_cost.return_value = None
            mock_service.return_value = mock_service_instance

            package_id = uuid4()
            response = client.post(f"/packages/{package_id}/calculate")

            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_recalculate_all_pending_success(self, client):
        """Тест массового пересчета ожидающих посылок."""

        with patch(
            "src.delivery_service.core.dependencies.get_package_service"
        ) as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.recalculate_all_pending.return_value = 5
            mock_service.return_value = mock_service_instance

            response = client.post("/packages/recalculate-pending")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["tasks_sent"] == 5
            assert "5 задач" in data["message"]


class TestPackageTypesAPI:
    """Тесты для API типов посылок."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    def test_list_package_types_success(self, client, sample_package_type):
        """Тест получения списка типов посылок."""

        with patch(
            "src.delivery_service.core.dependencies.get_package_type_repository"
        ) as mock_repo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.list.return_value = [sample_package_type]
            mock_repo.return_value = mock_repo_instance

            response = client.get("/package-types/")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == str(sample_package_type.id)
            assert data[0]["name"] == sample_package_type.name

    def test_create_package_type_success(self, client):
        """Тест успешного создания типа посылки."""

        with patch(
            "src.delivery_service.core.dependencies.get_package_type_repository"
        ) as mock_repo:
            created_type = type(
                "PackageType", (), {"id": uuid4(), "name": "Новый тип"}
            )()

            mock_repo_instance = AsyncMock()
            mock_repo_instance.create.return_value = created_type
            mock_repo.return_value = mock_repo_instance

            payload = {"name": "Новый тип"}
            response = client.post("/package-types/", json=payload)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == "Новый тип"
            assert data["id"] == str(created_type.id)

    def test_list_package_types_empty(self, client):
        """Тест получения пустого списка типов посылок."""

        with patch(
            "src.delivery_service.core.dependencies.get_package_type_repository"
        ) as mock_repo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.list.return_value = []
            mock_repo.return_value = mock_repo_instance

            response = client.get("/package-types/")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 0
