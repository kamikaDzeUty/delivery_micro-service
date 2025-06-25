# src/delivery_service/services/rate_service.py
import json
from decimal import Decimal
from redis.asyncio import Redis as AsyncRedis
import aiohttp

from src.delivery_service.core.config import settings

async def get_usd_to_rub_rate() -> Decimal:
    """
    Получить курс USD→RUB:
     1) пытаемся взять из Redis;
     2) если нет — делаем HTTP-запрос к ЦБ и кладём в Redis с TTL.
    Каждый раз создаётся свой Redis-клиент, "под" текущий asyncio-loop, и сразу же закрывается.
    """
    redis = AsyncRedis.from_url(
        str(settings.redis_url),
        encoding="utf-8",
        decode_responses=True,
    )
    key = "usd_to_rub"
    cached = await redis.get(key)
    if cached is not None:
        await redis.close()
        return Decimal(cached)

    async with aiohttp.ClientSession() as client:
        async with client.get(settings.cbr_api_url) as resp:
            try:
                data = await resp.json(content_type=None)
            except aiohttp.ContentTypeError:
                text = await resp.text()
                data = json.loads(text)
    rate = Decimal(data["Valute"]["USD"]["Value"])

    await redis.set(key, str(rate), ex=settings.rate_ttl_seconds)
    await redis.close()
    return rate
