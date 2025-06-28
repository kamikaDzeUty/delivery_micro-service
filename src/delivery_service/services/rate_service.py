import json
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
            logger.debug(f"Используется кешированный курс: {rate}")
            return rate

        # 2) Запрос к ЦБ
        logger.info("Получение курса USD/RUB из API ЦБ")
        try:
            async with self._http.get(settings.cbr_api_url) as resp:
                if resp.status != 200:
                    error_msg = f"API ЦБ вернул статус {resp.status}"
                    logger.error(error_msg)
                    raise aiohttp.ClientError(error_msg)
                
                text = await resp.text()
                data = json.loads(text)
                
                # API возвращает JSON в поле "Valute"→"USD"→"Value"
                rate = Decimal(str(data["Valute"]["USD"]["Value"]))
                logger.info(f"Получен курс от ЦБ: {rate}")

        except aiohttp.ClientError as e:
            logger.error(f"HTTP ошибка при получении курса из API ЦБ: {e}")
            rate = Decimal("100.0")  # Примерный курс
            logger.warning(f"Используется резервный курс из-за HTTP ошибки: {rate}")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON из API ЦБ: {e}")
            rate = Decimal("100.0")  # Примерный курс
            logger.warning(f"Используется резервный курс из-за ошибки JSON: {rate}")
        except KeyError as e:
            logger.error(f"Отсутствует ключ в ответе API ЦБ: {e}")
            rate = Decimal("100.0")  # Примерный курс
            logger.warning(f"Используется резервный курс из-за отсутствующего ключа: {rate}")
        except ValueError as e:
            logger.error(f"Некорректное значение курса из API ЦБ: {e}")
            rate = Decimal("100.0")  # Примерный курс
            logger.warning(f"Используется резервный курс из-за некорректного значения: {rate}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении курса из API ЦБ: {e}")
            rate = Decimal("100.0")  # Примерный курс
            logger.warning(f"Используется резервный курс из-за неожиданной ошибки: {rate}")

        # 3) Сохраняем в кеш
        try:
            await self._redis.set(
                self.CACHE_KEY,
                str(rate),
                ex=settings.rate_ttl_seconds,
            )
            logger.debug(f"Курс закеширован: {rate} на {settings.rate_ttl_seconds} секунд")
        except Exception as e:
            logger.error(f"Ошибка при кешировании курса: {e}")

        return rate

    async def clear_cache(self) -> None:
        """
        Очищает кеш курса валют.
        """
        try:
            await self._redis.delete(self.CACHE_KEY)
            logger.info("Кеш курса валют успешно очищен")
        except Exception as e:
            logger.error(f"Ошибка при очистке кеша курса: {e}")

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
            logger.error(f"Ошибка при получении информации о кеше: {e}")
            return {
                "has_cached_value": False,
                "ttl_seconds": None,
                "cached_rate": None,
                "error": str(e)
            }
