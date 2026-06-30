"""Board — grid dimensions and passability checks.

Why a dedicated class: movement, fog-of-war, and strategy all need
in-bounds and passability checks. Centralising them here means a single
fix propagates everywhere.
"""

from __future__ import annotations

import logging

__all__ = ["Board"]

log = logging.getLogger(__name__)


class Board:
    """Represents the game grid with configurable dimensions.

    Args:
        grid_size: [width, height] list from config.json.
    """

    def __init__(self, grid_size: list[int]) -> None:
        self.width: int = grid_size[0]
        self.height: int = grid_size[1]
        log.debug("Board created: %dx%d", self.width, self.height)

    def in_bounds(self, pos: tuple[int, int]) -> bool:
        """Return True if *pos* lies within the grid boundaries."""
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def is_passable(
        self, pos: tuple[int, int], barriers: frozenset[tuple[int, int]]
    ) -> bool:
        """Return True if *pos* is in-bounds and not blocked by a barrier."""
        return self.in_bounds(pos) and pos not in barriers

    def all_cells(self) -> list[tuple[int, int]]:
        """Return every cell on the board as a list of (x, y) tuples."""
        return [(x, y) for x in range(self.width) for y in range(self.height)]

    def __repr__(self) -> str:
        return f"Board(width={self.width}, height={self.height})"
