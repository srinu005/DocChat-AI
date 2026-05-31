"""Q&A endpoints — queue questions and poll for answers."""

import logging

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, status

from app.core.celery_app import celery_app
from app.models.schemas import (
    AnswerResponse,
    QuestionRequest,
    TaskResponse,
    TaskStatus,
)
from app.tasks.qa_tasks import answer_question_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["qa"])


@router.post(
    "/ask",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a question for background processing.",
)
async def ask_question(payload: QuestionRequest) -> TaskResponse:
    """Queue a question for the given session.

    Returns a ``task_id`` for polling via ``GET /api/answer/{task_id}``.
    """
    task = answer_question_task.delay(
        payload.session_id,
        payload.question,
    )
    logger.info(
        "Queued question task_id=%s session_id=%s",
        task.id,
        payload.session_id,
    )
    return TaskResponse(task_id=task.id)


@router.get(
    "/answer/{task_id}",
    response_model=AnswerResponse,
    summary="Poll for the result of a queued question.",
)
async def get_answer(task_id: str) -> AnswerResponse:
    """Return the current status and (when ready) the answer for *task_id*."""
    result: AsyncResult = AsyncResult(task_id, app=celery_app)
    state = result.state

    if state == TaskStatus.PENDING:
        return AnswerResponse(task_id=task_id, status=TaskStatus.PENDING)

    if state == TaskStatus.STARTED:
        return AnswerResponse(task_id=task_id, status=TaskStatus.STARTED)

    if state == TaskStatus.SUCCESS:
        data = result.result or {}
        # The task itself can return a FAILURE dict on handled errors
        task_status = TaskStatus(data.get("status", "SUCCESS"))
        return AnswerResponse(
            task_id=task_id,
            status=task_status,
            question=data.get("question"),
            answer=data.get("answer"),
            error=data.get("error"),
        )

    # Celery FAILURE (unhandled exception)
    return AnswerResponse(
        task_id=task_id,
        status=TaskStatus.FAILURE,
        error=str(result.result) if result.result else "Unknown error.",
    )
