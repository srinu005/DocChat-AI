# DocAI — Intelligent Document Q&A

Upload any document (PDF, DOCX, TXT, Markdown) and have a multi-turn conversation about its contents — powered by **Google Gemini**, **FastAPI**, **Celery**, and **Redis**.

---

## Architecture

```
┌────────────┐    ┌─────────────────────────────────────────┐
│  Browser   │───▶│  FastAPI  (api, upload, health routers)  │
│  HTML/CSS/ │◀───│  Jinja2 templates · Static files         │
│  JS        │    └───────────┬────────────┬─────────────────┘
└────────────┘                │            │
                              │ enqueue    │ dependency
                     ┌────────▼───────┐   ▼
                     │ Celery Worker  │  Redis
                     │ (qa_tasks.py)  │  ├── document text cache
                     │                │  ├── conversation history
                     │  GeminiService │  └── answer cache
                     └────────────────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| Background tasks | Celery 5 |
| Message broker & cache | Redis 7 |
| AI | Google Gemini 1.5 Flash |
| File parsing | PyPDF2, python-docx, aiofiles |
| Frontend | Vanilla HTML/CSS/JS (Jinja2) |
| Containerisation | Docker + Docker Compose |
| Testing | pytest + pytest-asyncio + fakeredis |

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/your-org/docai.git
cd docai
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 3. Run with Docker Compose

```bash
docker compose up --build
```

Open **http://localhost:8000** in your browser.

---

## Local Development (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start Redis (Docker one-liner)
docker run -d -p 6379:6379 redis:7-alpine

# Terminal 1 — API server
uvicorn app.main:app --reload

# Terminal 2 — Celery worker
celery -A app.core.celery_app.celery_app worker --loglevel=info
```

---

## Running Tests

```bash
pytest -v
```

Tests use **fakeredis** — no real Redis needed:

```
tests/
  test_file_parser.py   # FileParserService unit tests
  test_cache_service.py # CacheService unit tests
  test_api.py           # FastAPI endpoint integration tests
  test_ai_service.py    # GeminiService unit tests (fully mocked)
```

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload a document; returns `session_id` |
| `POST` | `/api/ask` | Queue a question; returns `task_id` |
| `GET` | `/api/answer/{task_id}` | Poll for the answer |
| `GET` | `/health` | Redis + app health check |
| `GET` | `/docs` | Swagger UI |

### Upload

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/path/to/document.pdf"
# → {"session_id": "uuid", "filename": "document.pdf", "message": "..."}
```

### Ask

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"session_id": "<uuid>", "question": "What are the main findings?"}'
# → {"task_id": "...", "status": "PENDING"}
```

### Poll

```bash
curl http://localhost:8000/api/answer/<task_id>
# → {"task_id": "...", "status": "SUCCESS", "answer": "..."}
```

---

## Design Principles

- **Single Responsibility** — each service/module has one job (`FileParserService`, `CacheService`, `GeminiService`)
- **Open/Closed** — AI model or cache backend can be swapped by extending, not modifying
- **Dependency Inversion** — FastAPI routes receive `redis` via DI; tests inject `fakeredis`
- **PEP 8** — consistent style enforced throughout
- **12-Factor** — config via environment variables, stateless containers

---

## Project Structure

```
docai/
├── app/
│   ├── api/          # FastAPI routers (upload, qa, health)
│   ├── core/         # Config, Redis client, Celery app
│   ├── models/       # Pydantic schemas
│   ├── services/     # FileParserService, CacheService, GeminiService
│   ├── tasks/        # Celery background tasks
│   └── main.py       # App factory
├── frontend/
│   ├── static/       # CSS + JS
│   └── templates/    # Jinja2 HTML
├── tests/            # pytest test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Git Workflow

```bash
# Feature branch
git checkout -b feature/your-feature

# Commit with conventional commit messages
git commit -m "feat: add conversation history export"
git commit -m "fix: handle empty PDF pages"
git commit -m "test: add cache TTL expiry tests"

# Push & open PR
git push origin feature/your-feature
```
