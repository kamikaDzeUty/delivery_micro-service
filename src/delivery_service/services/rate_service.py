import aiohttp
import redis.asyncio as redis

from src.delivery_service.core.config import settings

_redis = redis.from_url(settings.redis_url, decode_responses=True)

async def get_usd_to_rub_rate() -> float:
    key = "USD_RUB_RATE"
    cached = await _redis.get(key)
    if cached is not None:
        return float(cached)

    async with aiohttp.ClientSession() as session:
        async with session.get(settings.cbr_api_url) as resp:
            data = await resp.json()
    rate = data["Valute"]["USD"]["Value"]
    await _redis.set(key, rate, ex=settings.rate_ttl_seconds)
    return float(rate)
