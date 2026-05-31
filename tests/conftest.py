"""Shared pytest fixtures."""

import asyncio
import pytest
import fakeredis.aioredis as fakeredis

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.core.redis_client import get_redis
from app.services.cache_service import CacheService


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def fake_redis():
    """In-memory Redis substitute — no real Redis needed during tests."""
    client = fakeredis.FakeRedis(decode_responses=True)
    yield client
    await client.aclose()


@pytest.fixture
def cache_service(fake_redis):
    """CacheService backed by fakeredis."""
    return CacheService(fake_redis)


@pytest.fixture
def client(fake_redis):
    """FastAPI test client with Redis dependency overridden."""
    app.dependency_overrides[get_redis] = lambda: fake_redis
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
