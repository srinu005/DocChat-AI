"""Redis client factory — single shared connection pool."""

import redis.asyncio as aioredis
from app.core.config import settings


_redis_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """Return (or lazily create) the shared async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection — call on app shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
