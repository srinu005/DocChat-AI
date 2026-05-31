"""FastAPI application factory."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import health, qa, upload
from app.core.config import settings
from app.core.redis_client import close_redis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health.router)
    app.include_router(upload.router)
    app.include_router(qa.router)

    # Static files & templates
    app.mount(
        "/static",
        StaticFiles(directory="frontend/static"),
        name="static",
    )

    # Serve frontend index
    from fastapi import Request  # noqa: PLC0415
    from fastapi.responses import HTMLResponse  # noqa: PLC0415

    templates = Jinja2Templates(directory="frontend/templates")

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def serve_frontend(request: Request) -> HTMLResponse:
        return templates.TemplateResponse("index.html", {"request": request})

    # Lifecycle
    @app.on_event("shutdown")
    async def shutdown() -> None:
        await close_redis()

    return app


app = create_app()
