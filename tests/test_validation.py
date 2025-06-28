import pytest
from decimal import Decimal
from uuid import uuid4
from pydantic import ValidationError, BaseModel, Field, field_validator

from src.delivery_service.schemas.package import PackageCreate, PackageRead
from src.delivery_service.schemas.package_type import PackageTypeCreate, PackageTypeRead


class TestPackageValidation:
    """Тесты валидации схем пакетов"""

    def test_valid_package_create(self):
        """Тест создания валидного пакета"""
        valid_data = {
            "name": "Электроника",
            "weight": Decimal("2.5"),
            "declared_value": Decimal("500.00"),
            "type_id": uuid4()
        }
        
        package = PackageCreate(**valid_data)
        assert package.name == "Электроника"
        assert package.weight == Decimal("2.5")
        assert package.declared_value == Decimal("500.00")

    def test_package_name_validation(self):
        """Тест валидации названия пакета"""
        # Пустое название
        with pytest.raises(ValidationError) as exc_info:
            PackageCreate(
                name="",
                weight=Decimal("2.5"),
                declared_value=Decimal("500.00"),
                type_id=uuid4()
            )
        # В Pydantic v2 ошибки валидации имеют другой формат
        error_str = str(exc_info.value)
        assert "name" in error_str
        assert "String should have at least 1 character" in error_str

        # Слишком длинное название
        with pytest.raises(ValidationError) as exc_info:
            PackageCreate(
                name="a" * 101,  # 101 символ
                weight=Decimal("2.5"),
                declared_value=Decimal("500.00"),
                type_id=uuid4()
            )
        error_str = str(exc_info.value)
        assert "name" in error_str
        assert "String should have at most 100 characters" in error_str

        # Название с пробелами (должно обрезаться)
        package = PackageCreate(
            name="  Электроника  ",
            weight=Decimal("2.5"),
            declared_value=Decimal("500.00"),
            type_id=uuid4()
        )
        assert package.name == "Электроника"

    def test_package_weight_validation(self):
        """Тест валидации веса пакета"""
        # Отрицательный вес
        with pytest.raises(ValidationError) as exc_info:
            PackageCreate(
                name="Электроника",
                weight=Decimal("-1.0"),
                declared_value=Decimal("500.00"),
                type_id=uuid4()
            )
        error_str = str(exc_info.value)
        assert "weight" in error_str
        assert "Input should be greater than 0" in error_str

        # Слишком большой вес
        with pytest.raises(ValidationError) as exc_info:
            PackageCreate(
                name="Электроника",
                weight=Decimal("1001.0"),
                declared_value=Decimal("500.00"),
                type_id=uuid4()
            )
        error_str = str(exc_info.value)
        assert "weight" in error_str
        assert "Input should be less than or equal to 1000" in error_str

    def test_package_declared_value_validation(self):
        """Тест валидации объявленной стоимости"""
        # Отрицательная стоимость
        with pytest.raises(ValidationError) as exc_info:
            PackageCreate(
                name="Электроника",
                weight=Decimal("2.5"),
                declared_value=Decimal("-100.00"),
                type_id=uuid4()
            )
        error_str = str(exc_info.value)
        assert "declared_value" in error_str
        assert "Input should be greater than or equal to 0" in error_str

        # Слишком большая стоимость
        with pytest.raises(ValidationError) as exc_info:
            PackageCreate(
                name="Электроника",
                weight=Decimal("2.5"),
                declared_value=Decimal("1000001.00"),
                type_id=uuid4()
            )
        error_str = str(exc_info.value)
        assert "declared_value" in error_str
        assert "Input should be less than or equal to 1000000" in error_str

    def test_package_field_constraints(self):
        """Тест ограничений полей через Field"""
        # Вес меньше или равен 0
        with pytest.raises(ValidationError):
            PackageCreate(
                name="Электроника",
                weight=Decimal("0"),
                declared_value=Decimal("500.00"),
                type_id=uuid4()
            )

        # Вес больше 1000
        with pytest.raises(ValidationError):
            PackageCreate(
                name="Электроника",
                weight=Decimal("1000.1"),
                declared_value=Decimal("500.00"),
                type_id=uuid4()
            )

        # Объявленная стоимость меньше 0
        with pytest.raises(ValidationError):
            PackageCreate(
                name="Электроника",
                weight=Decimal("2.5"),
                declared_value=Decimal("-0.01"),
                type_id=uuid4()
            )

        # Объявленная стоимость больше 1000000
        with pytest.raises(ValidationError):
            PackageCreate(
                name="Электроника",
                weight=Decimal("2.5"),
                declared_value=Decimal("1000000.01"),
                type_id=uuid4()
            )


class TestPackageTypeValidation:
    """Тесты валидации схем типов пакетов"""

    def test_valid_package_type_create(self):
        """Тест создания валидного типа пакета"""
        valid_data = {
            "name": "Хрупкие предметы"
        }
        
        package_type = PackageTypeCreate(**valid_data)
        assert package_type.name == "Хрупкие предметы"

    def test_package_type_name_validation(self):
        """Тест валидации названия типа пакета"""
        # Пустое название
        with pytest.raises(ValidationError) as exc_info:
            PackageTypeCreate(name="")
        error_str = str(exc_info.value)
        assert "name" in error_str
        assert "String should have at least 1 character" in error_str

        # Слишком длинное название
        with pytest.raises(ValidationError) as exc_info:
            PackageTypeCreate(name="a" * 51)  # 51 символ
        error_str = str(exc_info.value)
        assert "name" in error_str
        assert "String should have at most 50 characters" in error_str

        # Название с пробелами (должно обрезаться)
        package_type = PackageTypeCreate(name="  Хрупкие предметы  ")
        assert package_type.name == "Хрупкие предметы"

    def test_package_type_field_constraints(self):
        """Тест ограничений полей через Field"""
        # Название короче минимальной длины
        with pytest.raises(ValidationError):
            PackageTypeCreate(name="")

        # Название длиннее максимальной длины
        with pytest.raises(ValidationError):
            PackageTypeCreate(name="a" * 51)


class TestPackageReadValidation:
    """Тесты валидации схем чтения пакетов"""

    def test_package_read_with_shipping_cost(self):
        """Тест чтения пакета со стоимостью доставки"""
        package_type = PackageTypeRead(
            id=uuid4(),
            name="Хрупкие предметы"
        )
        
        package = PackageRead(
            id=uuid4(),
            name="Электроника",
            weight=Decimal("2.5"),
            declared_value=Decimal("500.00"),
            shipping_cost=Decimal("7500.50"),
            type_id=uuid4(),
            type=package_type
        )
        
        assert package.shipping_cost == Decimal("7500.50")

    def test_package_read_without_shipping_cost(self):
        """Тест чтения пакета без стоимости доставки"""
        package_type = PackageTypeRead(
            id=uuid4(),
            name="Хрупкие предметы"
        )
        
        package = PackageRead(
            id=uuid4(),
            name="Электроника",
            weight=Decimal("2.5"),
            declared_value=Decimal("500.00"),
            shipping_cost=None,
            type_id=uuid4(),
            type=package_type
        )
        
        assert package.shipping_cost is None

    def test_package_read_shipping_cost_validation(self):
        """Тест валидации стоимости доставки в PackageRead"""
        package_type = PackageTypeRead(
            id=uuid4(),
            name="Хрупкие предметы"
        )
        
        # Отрицательная стоимость доставки
        with pytest.raises(ValidationError) as exc_info:
            PackageRead(
                id=uuid4(),
                name="Электроника",
                weight=Decimal("2.5"),
                declared_value=Decimal("500.00"),
                shipping_cost=Decimal("-100.00"),
                type_id=uuid4(),
                type=package_type
            )
        error_str = str(exc_info.value)
        assert "shipping_cost" in error_str
        assert "Input should be greater than or equal to 0" in error_str

@field_validator('name')
def validate_name(cls, v):
    if not v or not v.strip():
        raise ValueError('Название типа посылки не может быть пустым')
    return v.strip() 