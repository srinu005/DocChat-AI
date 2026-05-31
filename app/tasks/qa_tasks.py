"""Celery tasks — background Q&A processing."""

import asyncio
import logging

import nest_asyncio

from app.core.celery_app import celery_app
from app.core.redis_client import get_redis
from app.services.ai_service import GeminiService, AIServiceError
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a synchronous Celery task.
    
    Uses asyncio.run() for proper event loop handling in multiprocessing
    contexts (Celery workers), with nest_asyncio patch for safety.
    """
    # Patch asyncio to allow nested event loops in worker processes
    nest_asyncio.apply()
    return asyncio.run(coro)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=5)
def answer_question_task(self, session_id: str, question: str) -> dict:
    """Background task: retrieve document context, call Gemini, cache result.

    Args:
        session_id: The document session identifier.
        question: The user's question string.

    Returns:
        A dict with ``question``, ``answer``, and ``status`` keys.
    """
    try:
        redis = get_redis()
        cache = CacheService(redis)

        # 1. Check answer cache first
        cached = _run_async(cache.get_cached_answer(session_id, question))
        if cached:
            logger.info("Cache hit for session=%s", session_id)
            return {"question": question, "answer": cached, "status": "SUCCESS"}

        # 2. Fetch document text
        document_text = _run_async(cache.get_document(session_id))
        if not document_text:
            return {
                "question": question,
                "answer": None,
                "status": "FAILURE",
                "error": "Session expired or document not found.",
            }

        # 3. Fetch conversation history
        history = _run_async(cache.get_history(session_id))

        # 4. Call Gemini
        ai_service = GeminiService()
        answer = ai_service.answer_question(document_text, question, history)

        # 5. Persist turn in history and cache the answer
        _run_async(cache.append_message(session_id, "user", question))
        _run_async(cache.append_message(session_id, "model", answer))
        _run_async(cache.cache_answer(session_id, question, answer))

        return {"question": question, "answer": answer, "status": "SUCCESS"}

    except AIServiceError as exc:
        logger.error("AI error for session=%s: %s", session_id, exc)
        return {
            "question": question,
            "answer": None,
            "status": "FAILURE",
            "error": str(exc),
        }
    except Exception as exc:
        logger.exception("Unexpected error in answer_question_task")
        raise self.retry(exc=exc)
