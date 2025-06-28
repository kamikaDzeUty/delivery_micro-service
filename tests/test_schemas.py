from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.delivery_service.schemas.package import PackageCreate
from src.delivery_service.schemas.package_type import PackageTypeCreate, PackageTypeRead


class TestPackageSchemas:
    """Тесты для схем Package."""

    def test_package_create_valid(self):
        """Тест валидного создания посылки."""
        type_id = uuid4()
        data = {
            "name": "Тестовая посылка",
            "weight": Decimal("1.5"),
            "declared_value": Decimal("100.00"),
            "type_id": type_id,
        }
        package = PackageCreate(**data)

        assert package.name == "Тестовая посылка"
        assert package.weight == Decimal("1.5")
        assert package.declared_value == Decimal("100.00")
        assert package.type_id == type_id

    def test_package_create_name_validation(self):
        """Тест валидации названия посылки."""
        type_id = uuid4()

        # Пустое название
        with pytest.raises(ValidationError):
            PackageCreate(
                name="",
                weight=Decimal("1.0"),
                declared_value=Decimal("100.00"),
                type_id=type_id,
            )

        # Слишком длинное название
        with pytest.raises(ValidationError):
            PackageCreate(
                name="x" * 101,
                weight=Decimal("1.0"),
                declared_value=Decimal("100.00"),
                type_id=type_id,
            )

    def test_package_create_weight_validation(self):
        """Тест валидации веса посылки."""
        type_id = uuid4()

        # Отрицательный вес
        with pytest.raises(ValidationError):
            PackageCreate(
                name="Тест",
                weight=Decimal("-1.0"),
                declared_value=Decimal("100.00"),
                type_id=type_id,
            )

        # Нулевой вес
        with pytest.raises(ValidationError):
            PackageCreate(
                name="Тест",
                weight=Decimal("0"),
                declared_value=Decimal("100.00"),
                type_id=type_id,
            )

        # Слишком большой вес
        with pytest.raises(ValidationError):
            PackageCreate(
                name="Тест",
                weight=Decimal("1001"),
                declared_value=Decimal("100.00"),
                type_id=type_id,
            )

    def test_package_create_declared_value_validation(self):
        """Тест валидации объявленной стоимости."""
        type_id = uuid4()

        # Отрицательная стоимость
        with pytest.raises(ValidationError):
            PackageCreate(
                name="Тест",
                weight=Decimal("1.0"),
                declared_value=Decimal("-1.00"),
                type_id=type_id,
            )

        # Слишком большая стоимость
        with pytest.raises(ValidationError):
            PackageCreate(
                name="Тест",
                weight=Decimal("1.0"),
                declared_value=Decimal("1000001.00"),
                type_id=type_id,
            )

    def test_package_create_name_strip(self):
        """Тест обрезки пробелов в названии."""
        type_id = uuid4()
        package = PackageCreate(
            name="  Тест  ",
            weight=Decimal("1.0"),
            declared_value=Decimal("100.00"),
            type_id=type_id,
        )

        assert package.name == "Тест"


class TestPackageTypeSchemas:
    """Тесты для схем PackageType."""

    def test_package_type_create_valid(self):
        """Тест валидного создания типа посылки."""
        package_type = PackageTypeCreate(name="Электроника")
        assert package_type.name == "Электроника"

    def test_package_type_read_valid(self):
        """Тест валидного чтения типа посылки."""
        type_id = uuid4()
        package_type = PackageTypeRead(id=type_id, name="Документы")

        assert package_type.id == type_id
        assert package_type.name == "Документы"
