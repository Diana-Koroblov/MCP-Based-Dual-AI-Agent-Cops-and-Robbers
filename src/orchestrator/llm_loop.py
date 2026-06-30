"""LLM loop — sends prompts to Gemini and returns raw text responses.

Why a separate module: isolates all AI API calls so Phase 7 can replace
the direct Gemini call with a Gatekeeper-routed call without touching
the orchestrator logic above.

Empty or malformed responses raise LLMError and are treated as
technical failures by the caller (not silent fallbacks).
"""

from __future__ import annotations

import logging
from collections.abc import Callable

__all__ = ["LLMLoop", "LLMError"]

log = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when the LLM returns an empty, malformed, or API-level error."""


class LLMLoop:
    """Wraps Gemini API calls behind a swappable gateway.

    Args:
        model: Gemini model name (from config, e.g. 'gemini-1.5-flash').
        gateway: Callable[str, str] that accepts a prompt and returns raw
            text. Defaults to a direct Gemini call via google-generativeai.
            Phase 7 injects the Gatekeeper here.
    """

    def __init__(
        self,
        model: str = "gemini-1.5-flash",
        gateway: Callable[[str], str] | None = None,
    ) -> None:
        self._model = model
        self._gateway: Callable[[str], str] = gateway or self._default_gateway

    # ------------------------------------------------------------------
    # Default gateway — direct Gemini call (swapped out in Phase 7)
    # ------------------------------------------------------------------

    def _default_gateway(self, prompt: str) -> str:
        """Call Gemini directly via google-generativeai SDK."""
        try:
            import google.generativeai as genai  # type: ignore[import]
        except ImportError as exc:
            raise LLMError("google-generativeai is not installed.") from exc

        model_obj = genai.GenerativeModel(self._model)
        try:
            response = model_obj.generate_content(prompt)
            text: str = response.text
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"Gemini API error: {exc}") from exc

        if not text or not text.strip():
            raise LLMError("Gemini returned an empty response.")
        return text.strip()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ask(self, prompt: str) -> str:
        """Send *prompt* to the LLM and return the raw text response.

        Args:
            prompt: Full prompt string (built by PromptBuilder).

        Returns:
            Non-empty raw text from the LLM.

        Raises:
            LLMError: Empty, malformed, or API-level failure.
        """
        if not prompt.strip():
            raise LLMError("Prompt must not be empty.")
        log.debug("LLM ask: %d chars", len(prompt))
        result = self._gateway(prompt)
        if not result or not result.strip():
            raise LLMError("LLM gateway returned an empty response.")
        log.debug("LLM response: %d chars", len(result))
        return result
