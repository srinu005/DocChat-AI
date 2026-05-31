"""Integration tests for the FastAPI endpoints."""

import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient


# ── Upload endpoint ──────────────────────────────────────────────────────────

def test_upload_unsupported_type(client):
    """Uploading a .csv file must return 415."""
    data = {"file": ("data.csv", b"col1,col2\n1,2", "text/csv")}
    res = client.post("/api/upload", files=data)
    assert res.status_code == 415


def test_upload_valid_txt(client):
    """Uploading a .txt file should succeed and return a session_id."""
    with patch("app.api.upload._parser.extract_text", new=AsyncMock(return_value="doc text")):
        data = {"file": ("readme.txt", b"This is the document.", "text/plain")}
        res = client.post("/api/upload", files=data)

    assert res.status_code == 201
    body = res.json()
    assert "session_id" in body
    assert body["filename"] == "readme.txt"


def test_upload_file_too_large(client):
    """Files exceeding the size limit must return 413."""
    big_content = b"x" * (11 * 1024 * 1024)  # 11 MB
    data = {"file": ("big.txt", big_content, "text/plain")}
    res = client.post("/api/upload", files=data)
    assert res.status_code == 413


# ── Q&A endpoints ────────────────────────────────────────────────────────────

def test_ask_returns_task_id(client):
    """POST /api/ask must enqueue a task and return a task_id."""
    mock_task = MagicMock()
    mock_task.id = "fake-task-id-123"

    with patch("app.api.qa.answer_question_task.delay", return_value=mock_task):
        res = client.post("/api/ask", json={
            "session_id": "test-session",
            "question": "What is this document about?",
        })

    assert res.status_code == 202
    body = res.json()
    assert body["task_id"] == "fake-task-id-123"
    assert body["status"] == "PENDING"


def test_get_answer_pending(client):
    """GET /api/answer/{task_id} returns PENDING when task is not done."""
    mock_result = MagicMock()
    mock_result.state = "PENDING"
    mock_result.result = None

    with patch("app.api.qa.AsyncResult", return_value=mock_result):
        res = client.get("/api/answer/fake-task-id")

    assert res.status_code == 200
    assert res.json()["status"] == "PENDING"


def test_get_answer_success(client):
    """GET /api/answer/{task_id} returns answer when task succeeds."""
    mock_result = MagicMock()
    mock_result.state = "SUCCESS"
    mock_result.result = {
        "status": "SUCCESS",
        "question": "What is this?",
        "answer": "It is a test document.",
    }

    with patch("app.api.qa.AsyncResult", return_value=mock_result):
        res = client.get("/api/answer/fake-task-id")

    body = res.json()
    assert body["status"] == "SUCCESS"
    assert body["answer"] == "It is a test document."


def test_get_answer_failure(client):
    """GET /api/answer/{task_id} returns FAILURE on task error."""
    mock_result = MagicMock()
    mock_result.state = "FAILURE"
    mock_result.result = Exception("AI error")

    with patch("app.api.qa.AsyncResult", return_value=mock_result):
        res = client.get("/api/answer/bad-task-id")

    body = res.json()
    assert body["status"] == "FAILURE"


# ── Health endpoint ──────────────────────────────────────────────────────────

def test_health_endpoint(client):
    """GET /health must return status ok."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
