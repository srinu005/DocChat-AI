"""Tests for CacheService."""

import pytest

from app.services.cache_service import CacheService


@pytest.mark.asyncio
async def test_store_and_retrieve_document(cache_service):
    """Stored document text must be retrievable by session ID."""
    await cache_service.store_document("sess-1", "Hello document")
    result = await cache_service.get_document("sess-1")
    assert result == "Hello document"


@pytest.mark.asyncio
async def test_get_missing_document_returns_none(cache_service):
    """A session that was never stored should return None."""
    result = await cache_service.get_document("nonexistent-session")
    assert result is None


@pytest.mark.asyncio
async def test_conversation_history_append_and_retrieve(cache_service):
    """Messages appended to history should be returned in order."""
    await cache_service.append_message("sess-2", "user", "What is this?")
    await cache_service.append_message("sess-2", "model", "It is a test.")
    history = await cache_service.get_history("sess-2")

    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "What is this?"
    assert history[1]["role"] == "model"


@pytest.mark.asyncio
async def test_clear_history(cache_service):
    """Clearing history should leave an empty list."""
    await cache_service.append_message("sess-3", "user", "Question?")
    await cache_service.clear_history("sess-3")
    history = await cache_service.get_history("sess-3")
    assert history == []


@pytest.mark.asyncio
async def test_answer_cache_hit(cache_service):
    """Cached answers must be returned for the same session + question."""
    await cache_service.cache_answer("sess-4", "What is 2+2?", "4")
    cached = await cache_service.get_cached_answer("sess-4", "What is 2+2?")
    assert cached == "4"


@pytest.mark.asyncio
async def test_answer_cache_miss(cache_service):
    """A different question should return None (cache miss)."""
    await cache_service.cache_answer("sess-5", "Question A", "Answer A")
    result = await cache_service.get_cached_answer("sess-5", "Question B")
    assert result is None
