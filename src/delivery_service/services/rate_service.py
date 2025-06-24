# src/delivery_service/services/rate_service.py

import json
import aiohttp
from aiohttp import ContentTypeError
import redis.asyncio as redis

from src.delivery_service.core.config import settings

_redis = redis.from_url(str(settings.redis_url), decode_responses=True)


async def get_usd_to_rub_rate() -> float:
    key = "USD_RUB_RATE"
    cached = await _redis.get(key)
    if cached is not None:
        return float(cached)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(str(settings.cbr_api_url)) as resp:
                # отключаем проверку Content-Type, т.к. ЦБ отдает application/javascript
                try:
                    data = await resp.json(content_type=None)
                except ContentTypeError:
                    text = await resp.text()
                    data = json.loads(text)
    except Exception as network_error:
        raise RuntimeError("Ошибка сети при обращении к ЦБ РФ") from network_error

    rate = data["Valute"]["USD"]["Value"]
    await _redis.set(key, rate, ex=settings.rate_ttl_seconds)
    return float(rate)
