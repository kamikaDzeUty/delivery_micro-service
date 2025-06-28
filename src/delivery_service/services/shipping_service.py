from decimal import Decimal
from src.delivery_service.services.rate_service import RateService
from src.delivery_service.core.logging import get_logger

logger = get_logger(__name__)


class ShippingService:
    """
    Сервис для расчета стоимости доставки.
    """

    def __init__(self, rate_service: RateService):
        self._rate_service = rate_service

    async def calculate_shipping_cost(
        self,
        weight_kg: Decimal,
        declared_value_usd: Decimal,
    ) -> Decimal:
        """
        Рассчитывает стоимость доставки в рублях.
        
        Args:
            weight_kg: Вес посылки в килограммах
            declared_value_usd: Объявленная стоимость в USD
            
        Returns:
            Стоимость доставки в рублях
        """
        logger.debug(f"Расчет стоимости доставки: вес={weight_kg}кг, стоимость=${declared_value_usd}")
        
        # Получаем актуальный курс USD/RUB
        rate = await self._rate_service.get_usd_to_rub_rate()
        logger.debug(f"Используется курс USD/RUB: {rate}")
        
        # Базовая стоимость за вес (100 руб/кг)
        base_weight_cost = weight_kg * Decimal("100.0")
        
        # Дополнительная стоимость за объявленную ценность (1% от стоимости в рублях)
        declared_value_rub = declared_value_usd * rate
        value_cost = declared_value_rub * Decimal("0.01")
        
        # Итоговая стоимость
        total_cost = base_weight_cost + value_cost
        
        logger.info(f"Стоимость доставки рассчитана: базовая={base_weight_cost}, за ценность={value_cost}, итого={total_cost}")
        
        return total_cost.quantize(Decimal("0.01"))
