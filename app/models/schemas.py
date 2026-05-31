"""Domain models and API schemas."""

from enum import Enum
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Possible states of a background Celery task."""

    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class UploadResponse(BaseModel):
    """Returned after a successful file upload."""

    session_id: str = Field(..., description="Unique session identifier.")
    filename: str
    message: str = "File uploaded successfully."


class QuestionRequest(BaseModel):
    """Payload for submitting a question."""

    session_id: str = Field(..., description="Session returned by /upload.")
    question: str = Field(..., min_length=3, max_length=2000)


class TaskResponse(BaseModel):
    """Immediate response when a question is queued."""

    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    message: str = "Question queued for processing."


class AnswerResponse(BaseModel):
    """Final answer delivered after task completion."""

    task_id: str
    status: TaskStatus
    question: str | None = None
    answer: str | None = None
    error: str | None = None


class ConversationMessage(BaseModel):
    """A single turn in the conversation history."""

    role: str  # "user" | "model"
    content: str


class HealthResponse(BaseModel):
    """Service health-check payload."""

    status: str = "ok"
    redis: bool = False
    version: str
