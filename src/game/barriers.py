"""Barrier placement manager for the Cop agent.

Why a dedicated class: barrier state (count, positions) is mutated during a
sub-game and must be reset between sub-games. Encapsulating it here prevents
accidental state leakage and keeps turn_manager.py focused on turn logic.
"""

from __future__ import annotations

import logging

__all__ = ["BarrierManager"]

log = logging.getLogger(__name__)


class BarrierManager:
    """Tracks barrier placements and enforces the per-sub-game cap.

    Args:
        max_barriers: Maximum number of barriers the Cop may place.
            Must match config['max_barriers'].
    """

    def __init__(self, max_barriers: int) -> None:
        self._max = max_barriers
        self._placed: set[tuple[int, int]] = set()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def barriers(self) -> frozenset[tuple[int, int]]:
        """Return the current barrier positions as an immutable frozenset."""
        return frozenset(self._placed)

    @property
    def count(self) -> int:
        """Return the number of barriers placed so far this sub-game."""
        return len(self._placed)

    @property
    def remaining(self) -> int:
        """Return how many more barriers the Cop may place."""
        return self._max - self._placed.__len__()

    def can_place(self) -> bool:
        """Return True if the cap has not been reached."""
        return len(self._placed) < self._max

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def place(self, pos: tuple[int, int]) -> bool:
        """Attempt to place a barrier at *pos*.

        A placement is rejected (returns False, does NOT consume a turn) if:
        - The cap of *max_barriers* has already been reached.
        - A barrier already exists at *pos*.

        Why log at WARNING: a rejected placement is an agent error that should
        be visible in logs without crashing the game.
        """
        if not self.can_place():
            log.warning(
                "Barrier rejected: cap of %d already reached (%d placed).",
                self._max,
                len(self._placed),
            )
            return False
        if pos in self._placed:
            log.warning("Barrier rejected: cell %s already has a barrier.", pos)
            return False
        self._placed.add(pos)
        log.info("Barrier placed at %s (%d/%d used).", pos, len(self._placed), self._max)
        return True

    def reset(self) -> None:
        """Clear all barriers — called between sub-games."""
        log.debug("BarrierManager reset (%d barriers cleared).", len(self._placed))
        self._placed = set()
