from decimal import Decimal, ROUND_HALF_UP

from src.delivery_service.services.rate_service import get_usd_to_rub_rate

async def calculate_shipping_cost(
    weight: Decimal,
    declared_value: Decimal,
) -> Decimal:
    """
    Рассчитывает стоимость доставки в рублях на основе веса и объявленной стоимости.
    Формула:
      USD = вес * 0.5 + стоимость * 0.01
      RUB = USD * курс USD->RUB
    Возвращает округлённую сумму с точностью до копеек.
    """
    rate = await get_usd_to_rub_rate()
    cost_usd = weight * Decimal("0.5") + declared_value * Decimal("0.01")
    cost_rub = cost_usd * Decimal(str(rate))
    return cost_rub.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
