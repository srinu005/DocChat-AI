"""Upload endpoint — accepts files and stores extracted text in Redis."""

import logging
import os
import pathlib
import uuid

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.redis_client import get_redis
from app.models.schemas import UploadResponse
from app.services.cache_service import CacheService
from app.services.file_parser import FileParserService, UnsupportedFileTypeError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["upload"])

_parser = FileParserService()


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document to start a Q&A session.",
)
async def upload_document(
    file: UploadFile = File(...),
    redis: aioredis.Redis = Depends(get_redis),
) -> UploadResponse:
    """Upload a PDF, DOCX, TXT, or MD file.

    Returns a ``session_id`` that must be included in subsequent
    ``/ask`` requests.
    """
    # Validate extension
    suffix = pathlib.Path(file.filename or "").suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type '{suffix}'. "
                f"Allowed: {settings.allowed_extensions}"
            ),
        )

    # Validate size
    contents = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.max_file_size_mb} MB.",
        )

    # Save temporarily
    os.makedirs(settings.upload_dir, exist_ok=True)
    session_id = str(uuid.uuid4())
    tmp_path = os.path.join(settings.upload_dir, f"{session_id}{suffix}")

    async with aiofiles.open(tmp_path, "wb") as fh:
        await fh.write(contents)

    # Extract text and store in Redis
    try:
        text = await _parser.extract_text(tmp_path)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Text extraction failed for %s", tmp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not extract text from the uploaded file.",
        ) from exc
    finally:
        # Remove temp file regardless of outcome
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    cache = CacheService(redis)
    await cache.store_document(session_id, text)

    logger.info("Uploaded '%s' → session_id=%s", file.filename, session_id)
    return UploadResponse(session_id=session_id, filename=file.filename or "unknown")
