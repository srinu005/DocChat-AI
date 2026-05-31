"""Document text-extraction service.

Follows the Single Responsibility Principle — only responsible for
converting uploaded files into plain text strings.
"""

import io
import pathlib

import aiofiles


class UnsupportedFileTypeError(ValueError):
    """Raised when a file extension is not supported."""


class FileParserService:
    """Extract raw text from PDF, DOCX, TXT, and MD files."""

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def extract_text(self, file_path: str) -> str:
        """Return the full text content of *file_path*.

        Args:
            file_path: Absolute path to the uploaded file on disk.

        Returns:
            Extracted text as a single string.

        Raises:
            UnsupportedFileTypeError: If the extension is not recognised.
        """
        suffix = pathlib.Path(file_path).suffix.lower()
        extractor = self._get_extractor(suffix)
        return await extractor(file_path)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_extractor(self, suffix: str):
        """Return the correct async extractor coroutine for *suffix*."""
        mapping = {
            ".pdf": self._extract_pdf,
            ".txt": self._extract_plain,
            ".md": self._extract_plain,
            ".docx": self._extract_docx,
        }
        extractor = mapping.get(suffix)
        if extractor is None:
            raise UnsupportedFileTypeError(
                f"File type '{suffix}' is not supported. "
                f"Allowed: {list(mapping.keys())}"
            )
        return extractor

    async def _extract_plain(self, file_path: str) -> str:
        """Read a plain-text or Markdown file."""
        async with aiofiles.open(file_path, encoding="utf-8", errors="replace") as fh:
            return await fh.read()

    async def _extract_pdf(self, file_path: str) -> str:
        """Extract text from every page of a PDF."""
        try:
            import PyPDF2  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError("PyPDF2 is required for PDF extraction.") from exc

        async with aiofiles.open(file_path, "rb") as fh:
            raw = await fh.read()

        reader = PyPDF2.PdfReader(io.BytesIO(raw))
        pages = [
            page.extract_text() or ""
            for page in reader.pages
        ]
        return "\n".join(pages)

    async def _extract_docx(self, file_path: str) -> str:
        """Extract text from a Microsoft Word document."""
        try:
            import docx  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError("python-docx is required for DOCX extraction.") from exc

        doc = docx.Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(paragraphs)
