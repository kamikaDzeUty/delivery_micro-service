import json
import logging
from decimal import Decimal

import aiohttp
from redis.asyncio import Redis

from src.delivery_service.core.config import settings

logger = logging.getLogger(__name__)


class RateService:
    """
    Сервис для получения и кеширования курса USD→RUB.
    """

    CACHE_KEY = "usd_to_rub_rate"

    def __init__(self, http_client: aiohttp.ClientSession, redis_client: Redis):
        self._http = http_client
        self._redis = redis_client

    async def get_usd_to_rub_rate(self) -> Decimal:
        """
        Получает курс USD к RUB с кешированием.
        """
        # 1) Попробуем взять из кеша
        cached = await self._redis.get(self.CACHE_KEY)
        if cached is not None:
            logger.debug(f"Using cached rate: {cached}")
            return Decimal(cached.decode())

        # 2) Запрос к ЦБ
        logger.info("Fetching USD/RUB rate from CBR API")
        try:
            async with self._http.get(settings.cbr_api_url) as resp:
                if resp.status != 200:
                    raise aiohttp.ClientError(f"CBR API returned status {resp.status}")
                
                text = await resp.text()
                data = json.loads(text)
                
                # API возвращает JSON в поле "Valute"→"USD"→"Value"
                rate = Decimal(str(data["Valute"]["USD"]["Value"]))
                logger.info(f"Received rate from CBR: {rate}")

        except (aiohttp.ClientError, json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Error fetching rate from CBR API: {e}")
            # Возвращаем fallback значение
            rate = Decimal("100.0")  # Примерный курс
            logger.warning(f"Using fallback rate: {rate}")

        # 3) Сохраняем в кеш
        try:
            await self._redis.set(
                self.CACHE_KEY,
                str(rate),
                ex=settings.rate_ttl_seconds,
            )
            logger.debug(f"Cached rate: {rate}")
        except Exception as e:
            logger.error(f"Error caching rate: {e}")

        return rate

    async def clear_cache(self) -> None:
        """
        Очищает кеш курса валют.
        """
        try:
            await self._redis.delete(self.CACHE_KEY)
            logger.info("Rate cache cleared")
        except Exception as e:
            logger.error(f"Error clearing rate cache: {e}")
