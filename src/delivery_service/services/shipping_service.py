from decimal import Decimal

from src.delivery_service.core.config import settings
from src.delivery_service.services.rate_service import RateService

class ShippingService:
    """
    Сервис, который рассчитывает стоимость доставки.
    """

    def __init__(self, rate_service: RateService):
        self._rate = rate_service

    async def calculate_shipping_cost(
        self,
        weight_kg: Decimal,
        declared_value_usd: Decimal,
    ) -> Decimal:
        """
        Формула расчёта:
          стоимость = weight_kg * rate * settings.weight_coefficient
                    + declared_value_usd * rate * settings.value_coefficient
        """
        rate = await self._rate.get_usd_to_rub_rate()

        weight_cost = (
            weight_kg
            * rate
            * Decimal(settings.weight_coefficient)
        )
        value_cost = (
            declared_value_usd
            * rate
            * Decimal(settings.value_coefficient)
        )
        total = weight_cost + value_cost
        return total.quantize(Decimal("0.01"))
