"""Custom exceptions for the game engine.

Why a dedicated module: exceptions are raised in multiple game modules and
caught in sub_game / full_game. A single location prevents circular imports
and makes error taxonomy visible at a glance.
"""

from __future__ import annotations

__all__ = ["TechnicalFailureError", "InvalidActionError", "GameNotStartedError"]


class TechnicalFailureError(RuntimeError):
    """Raised when a sub-game cannot continue due to a technical problem.

    Examples: LLM timeout, MCP server unreachable, empty LLM response.
    The sub-game runner catches this and schedules an automatic rerun.
    """


class InvalidActionError(ValueError):
    """Raised when an agent submits an action that violates game rules.

    Examples: moving out of bounds, placing a 6th barrier, moving into a barrier.
    """


class GameNotStartedError(RuntimeError):
    """Raised when a game-lifecycle method is called before start_game()."""
