"""Google Gemini AI service for document-grounded question answering."""

from typing import Any

import google.generativeai as genai

from app.core.config import settings


class AIServiceError(RuntimeError):
    """Raised when the AI provider returns an unexpected error."""


class GeminiService:
    """Wrap the Google Generative AI SDK to answer questions about documents.

    Follows the Open/Closed Principle — swap the underlying model by
    subclassing or changing ``settings.gemini_model`` without modifying
    callers.
    """

    _SYSTEM_PROMPT = (
        "You are a helpful, accurate document assistant. "
        "Answer the user's question using ONLY the information found in the "
        "provided document context. "
        "If the answer cannot be found in the document, say so clearly. "
        "Be concise, factual, and cite specific parts of the document "
        "when relevant."
    )

    def __init__(self) -> None:
        genai.configure(api_key=settings.google_api_key)
        self._model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=self._SYSTEM_PROMPT,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def answer_question(
        self,
        document_text: str,
        question: str,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generate an answer grounded in *document_text*.

        Args:
            document_text: The full extracted text of the uploaded file.
            question: The user's current question.
            history: Previous turns as ``[{"role": ..., "content": ...}]``.

        Returns:
            The model's answer as a plain string.

        Raises:
            AIServiceError: On any error from the Gemini API.
        """
        try:
            chat = self._model.start_chat(
                history=self._build_chat_history(history or [])
            )
            prompt = self._build_prompt(document_text, question)
            response = chat.send_message(prompt)
            return response.text
        except Exception as exc:
            raise AIServiceError(f"Gemini API error: {exc}") from exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_prompt(document_text: str, question: str) -> str:
        """Construct a prompt that includes the document context."""
        return (
            f"### Document Context\n\n{document_text}\n\n"
            f"### Question\n\n{question}"
        )

    @staticmethod
    def _build_chat_history(
        history: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Convert stored history format to Gemini SDK format."""
        return [
            {"role": turn["role"], "parts": [turn["content"]]}
            for turn in history
        ]
