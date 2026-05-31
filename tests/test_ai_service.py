"""Tests for GeminiService (mocked — no real API calls)."""

import pytest
from unittest.mock import MagicMock, patch

from app.services.ai_service import GeminiService, AIServiceError


@pytest.fixture
def mock_genai():
    """Patch google.generativeai so no real API call is made."""
    with patch("app.services.ai_service.genai") as mock:
        model_instance = MagicMock()
        mock.GenerativeModel.return_value = model_instance
        yield mock, model_instance


def test_answer_question_returns_text(mock_genai):
    """answer_question should return the model's text response."""
    _, model_instance = mock_genai
    chat = MagicMock()
    chat.send_message.return_value = MagicMock(text="The document is about testing.")
    model_instance.start_chat.return_value = chat

    service = GeminiService()
    result = service.answer_question("doc text", "What is this?")

    assert result == "The document is about testing."


def test_answer_question_with_history(mock_genai):
    """History should be converted and passed to start_chat."""
    _, model_instance = mock_genai
    chat = MagicMock()
    chat.send_message.return_value = MagicMock(text="Answer with history context.")
    model_instance.start_chat.return_value = chat

    history = [
        {"role": "user", "content": "Previous question?"},
        {"role": "model", "content": "Previous answer."},
    ]
    service = GeminiService()
    result = service.answer_question("doc text", "Follow-up?", history=history)

    assert result == "Answer with history context."
    call_args = model_instance.start_chat.call_args
    passed_history = call_args.kwargs.get("history", [])
    assert len(passed_history) == 2
    assert passed_history[0]["role"] == "user"


def test_answer_question_raises_ai_service_error(mock_genai):
    """API exceptions should be wrapped in AIServiceError."""
    _, model_instance = mock_genai
    chat = MagicMock()
    chat.send_message.side_effect = RuntimeError("quota exceeded")
    model_instance.start_chat.return_value = chat

    service = GeminiService()
    with pytest.raises(AIServiceError, match="Gemini API error"):
        service.answer_question("doc text", "Any question?")
