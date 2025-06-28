import json
import logging
from decimal import Decimal

import aiohttp
from redis.asyncio import Redis

from src.delivery_service.core.config import settings
from src.delivery_service.core.logging import get_logger

logger = get_logger(__name__)


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
            rate = Decimal(cached.decode())
            logger.debug(f"Using cached rate: {rate}")
            return rate

        # 2) Запрос к ЦБ
        logger.info("Fetching USD/RUB rate from CBR API")
        try:
            async with self._http.get(settings.cbr_api_url) as resp:
                if resp.status != 200:
                    error_msg = f"CBR API returned status {resp.status}"
                    logger.error(error_msg)
                    raise aiohttp.ClientError(error_msg)
                
                text = await resp.text()
                data = json.loads(text)
                
                # API возвращает JSON в поле "Valute"→"USD"→"Value"
                rate = Decimal(str(data["Valute"]["USD"]["Value"]))
                logger.info(f"Received rate from CBR: {rate}")

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error fetching rate from CBR API: {e}")
            rate = Decimal("100.0")  # Примерный курс
            logger.warning(f"Using fallback rate due to HTTP error: {rate}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error from CBR API: {e}")
            rate = Decimal("100.0")  # Примерный курс
            logger.warning(f"Using fallback rate due to JSON error: {rate}")
        except KeyError as e:
            logger.error(f"Missing key in CBR API response: {e}")
            rate = Decimal("100.0")  # Примерный курс
            logger.warning(f"Using fallback rate due to missing key: {rate}")
        except ValueError as e:
            logger.error(f"Invalid rate value from CBR API: {e}")
            rate = Decimal("100.0")  # Примерный курс
            logger.warning(f"Using fallback rate due to invalid value: {rate}")
        except Exception as e:
            logger.error(f"Unexpected error fetching rate from CBR API: {e}")
            rate = Decimal("100.0")  # Примерный курс
            logger.warning(f"Using fallback rate due to unexpected error: {rate}")

        # 3) Сохраняем в кеш
        try:
            await self._redis.set(
                self.CACHE_KEY,
                str(rate),
                ex=settings.rate_ttl_seconds,
            )
            logger.debug(f"Cached rate: {rate} for {settings.rate_ttl_seconds} seconds")
        except Exception as e:
            logger.error(f"Error caching rate: {e}")

        return rate

    async def clear_cache(self) -> None:
        """
        Очищает кеш курса валют.
        """
        try:
            await self._redis.delete(self.CACHE_KEY)
            logger.info("Rate cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing rate cache: {e}")

    async def get_cache_info(self) -> dict:
        """
        Получает информацию о кеше курса валют.
        """
        try:
            ttl = await self._redis.ttl(self.CACHE_KEY)
            cached_value = await self._redis.get(self.CACHE_KEY)
            
            return {
                "has_cached_value": cached_value is not None,
                "ttl_seconds": ttl if ttl > 0 else None,
                "cached_rate": Decimal(cached_value.decode()) if cached_value else None
            }
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {
                "has_cached_value": False,
                "ttl_seconds": None,
                "cached_rate": None,
                "error": str(e)
            }
