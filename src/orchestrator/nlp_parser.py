"""NLP parser — extracts structured intentions from raw LLM text.

Why keyword matching over a second LLM call: lower latency, no extra
API cost, and the output format is constrained enough that regex is reliable.
Confidence < 0.5 signals the strategy module should decide instead.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from src.game.actions import Direction

__all__ = ["IntentionResult", "NLPParser"]

log = logging.getLogger(__name__)

# Matches bare numeric coordinates — forbidden in LLM output.
_COORD_RE = re.compile(r"[\(\[]\s*\d+\s*,\s*\d+\s*[\)\]]")

# Ordered: longer/more-specific keywords first to prevent prefix matches.
_DIRECTION_KEYWORDS: list[tuple[str, Direction]] = [
    ("northeast", Direction.NE),
    ("northwest", Direction.NW),
    ("southeast", Direction.SE),
    ("southwest", Direction.SW),
    ("north", Direction.N),
    ("south", Direction.S),
    ("east", Direction.E),
    ("west", Direction.W),
    (" ne ", Direction.NE),
    (" nw ", Direction.NW),
    (" se ", Direction.SE),
    (" sw ", Direction.SW),
    (" n ", Direction.N),
    (" s ", Direction.S),
    (" e ", Direction.E),
    (" w ", Direction.W),
]


@dataclass
class IntentionResult:
    """Structured output of the NLP parser.

    Attributes:
        action: Parsed Direction or 'place_barrier' string; None if unknown.
        direction: The Direction value when action is a move; None otherwise.
        target_cell: Always None — coordinates are forbidden in LLM output.
        confidence: 0.0–1.0; < 0.5 means the strategy module should decide.
        raw_text: The original LLM output, preserved for logging/audit.
        message: The NL message extracted from the MESSAGE: line.
    """

    action: Direction | str | None
    direction: Direction | None
    target_cell: None
    confidence: float
    raw_text: str
    message: str = field(default="")


class NLPParser:
    """Parses raw LLM text into an IntentionResult via keyword matching."""

    def parse(self, text: str) -> IntentionResult:
        """Extract action, direction, confidence, and message from *text*.

        Args:
            text: Raw LLM response (may contain ACTION: and MESSAGE: lines).

        Returns:
            IntentionResult; confidence < 0.5 indicates no reliable parse.
        """
        log.debug("NLPParser.parse input: %r", text[:120])

        message = self._extract_message(text)
        action_line = self._extract_action_line(text)

        # Barrier takes priority over direction keywords
        if "place_barrier" in action_line.lower() or "barrier" in action_line.lower():
            log.debug("Parsed action: place_barrier (confidence=0.9)")
            return IntentionResult(
                action="place_barrier",
                direction=None,
                target_cell=None,
                confidence=0.9,
                raw_text=text,
                message=message,
            )

        direction = self._extract_direction(action_line)
        if direction is not None:
            log.debug("Parsed direction: %s (confidence=0.85)", direction)
            return IntentionResult(
                action=direction,
                direction=direction,
                target_cell=None,
                confidence=0.85,
                raw_text=text,
                message=message,
            )

        log.debug("No reliable action found (confidence=0.3)")
        return IntentionResult(
            action=None,
            direction=None,
            target_cell=None,
            confidence=0.3,
            raw_text=text,
            message=message,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_action_line(self, text: str) -> str:
        """Return the content after 'ACTION:'; fall back to full text."""
        for line in text.splitlines():
            if line.upper().startswith("ACTION:"):
                return line.split(":", 1)[1].strip()
        return text

    def _extract_message(self, text: str) -> str:
        """Return the content after 'MESSAGE:', or empty string."""
        for line in text.splitlines():
            if line.upper().startswith("MESSAGE:"):
                return line.split(":", 1)[1].strip()
        return ""

    def _extract_direction(self, text: str) -> Direction | None:
        """Scan *text* for the first matching direction keyword."""
        padded = f" {text.lower()} "
        for keyword, direction in _DIRECTION_KEYWORDS:
            if keyword in padded:
                return direction
        return None

    @staticmethod
    def has_coordinate_leak(text: str) -> bool:
        """Return True if *text* contains forbidden numeric coordinates."""
        return bool(_COORD_RE.search(text))
