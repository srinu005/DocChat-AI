"""Cache service — thin wrapper around Redis for document storage and Q&A caching."""

import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings


class CacheService:
    """Provide typed get/set helpers for Redis-backed caching.

    Follows the Interface Segregation Principle — callers depend only on
    the cache abstraction, not on the underlying Redis client.
    """

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self._redis = redis_client
        self._ttl = settings.cache_ttl_seconds

    # ------------------------------------------------------------------
    # Document text
    # ------------------------------------------------------------------

    async def store_document(self, session_id: str, text: str) -> None:
        """Persist extracted document text for the given session."""
        key = self._doc_key(session_id)
        await self._redis.set(key, text, ex=self._ttl)

    async def get_document(self, session_id: str) -> str | None:
        """Retrieve stored document text; ``None`` if expired or missing."""
        return await self._redis.get(self._doc_key(session_id))

    # ------------------------------------------------------------------
    # Conversation history
    # ------------------------------------------------------------------

    async def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Append a conversation turn to the session history list."""
        key = self._history_key(session_id)
        message = json.dumps({"role": role, "content": content})
        await self._redis.rpush(key, message)
        await self._redis.expire(key, self._ttl)

    async def get_history(self, session_id: str) -> list[dict[str, Any]]:
        """Return the full conversation history as a list of dicts."""
        key = self._history_key(session_id)
        raw_messages = await self._redis.lrange(key, 0, -1)
        return [json.loads(m) for m in raw_messages]

    async def clear_history(self, session_id: str) -> None:
        """Delete the conversation history for a session."""
        await self._redis.delete(self._history_key(session_id))

    # ------------------------------------------------------------------
    # Answer cache (avoid re-computing identical questions)
    # ------------------------------------------------------------------

    async def get_cached_answer(
        self,
        session_id: str,
        question: str,
    ) -> str | None:
        """Return a previously computed answer or ``None``."""
        return await self._redis.get(self._answer_key(session_id, question))

    async def cache_answer(
        self,
        session_id: str,
        question: str,
        answer: str,
    ) -> None:
        """Store an answer for later retrieval."""
        key = self._answer_key(session_id, question)
        await self._redis.set(key, answer, ex=self._ttl)

    # ------------------------------------------------------------------
    # Key builders
    # ------------------------------------------------------------------

    @staticmethod
    def _doc_key(session_id: str) -> str:
        return f"docai:doc:{session_id}"

    @staticmethod
    def _history_key(session_id: str) -> str:
        return f"docai:history:{session_id}"

    @staticmethod
    def _answer_key(session_id: str, question: str) -> str:
        # Normalise question to create a stable cache key.
        normalised = question.strip().lower()
        return f"docai:answer:{session_id}:{hash(normalised)}"
