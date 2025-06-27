import json
from decimal import Decimal

import aiohttp
from redis.asyncio import Redis

from src.delivery_service.core.config import settings


class RateService:
    """
    Сервис для получения и кеширования курса USD→RUB.
    """

    CACHE_KEY = "usd_to_rub_rate"

    def __init__(self, http_client: aiohttp.ClientSession, redis_client: Redis):
        self._http = http_client
        self._redis = redis_client

    async def get_usd_to_rub_rate(self) -> Decimal:
        # 1) Попробуем взять из кеша
        cached = await self._redis.get(self.CACHE_KEY)
        if cached is not None:
            return Decimal(cached)

        # 2) Запрос к ЦБ
        resp = await self._http.get(settings.cbr_api_url)
        text = await resp.text()
        data = json.loads(text)
        # API возвращает JSON в поле "Valute"→"USD"→"Value"
        rate = Decimal(data["Valute"]["USD"]["Value"])

        # 3) Сохраняем в кеш
        await self._redis.set(
            self.CACHE_KEY,
            str(rate),
            ex=settings.rate_ttl_seconds,
        )
        return rate
