"""Health-check endpoint."""

from fastapi import APIRouter, Depends
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.redis_client import get_redis
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Service health check.")
async def health_check(
    redis: aioredis.Redis = Depends(get_redis),
) -> HealthResponse:
    """Return OK with Redis connectivity status."""
    redis_ok = False
    try:
        redis_ok = await redis.ping()
    except Exception:
        pass

    return HealthResponse(
        status="ok",
        redis=redis_ok,
        version=settings.app_version,
    )
