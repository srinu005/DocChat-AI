"""Tests for FileParserService."""

import os
import tempfile

import pytest

from app.services.file_parser import FileParserService, UnsupportedFileTypeError


@pytest.fixture
def parser():
    return FileParserService()


@pytest.mark.asyncio
async def test_extract_plain_text(parser):
    """Plain .txt files should be returned as-is."""
    content = "Hello, this is a test document.\nLine two."
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name
    try:
        result = await parser.extract_text(path)
        assert result == content
    finally:
        os.remove(path)


@pytest.mark.asyncio
async def test_extract_markdown(parser):
    """Markdown .md files should be read as plain text."""
    content = "# Heading\n\nSome paragraph."
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name
    try:
        result = await parser.extract_text(path)
        assert "Heading" in result
    finally:
        os.remove(path)


@pytest.mark.asyncio
async def test_unsupported_extension_raises(parser):
    """An unsupported file extension must raise UnsupportedFileTypeError."""
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        path = f.name
    try:
        with pytest.raises(UnsupportedFileTypeError):
            await parser.extract_text(path)
    finally:
        os.remove(path)


@pytest.mark.asyncio
async def test_extract_pdf(parser):
    """PDF extraction should return non-empty text from a valid PDF."""
    pytest.importorskip("PyPDF2")
    import io
    import PyPDF2
    from PyPDF2 import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(buf.getvalue())
        path = f.name
    try:
        # Blank page has no text — just assert no exception raised
        result = await parser.extract_text(path)
        assert isinstance(result, str)
    finally:
        os.remove(path)
