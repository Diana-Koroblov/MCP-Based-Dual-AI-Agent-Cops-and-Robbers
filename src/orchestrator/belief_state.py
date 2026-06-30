"""Belief state — probability distribution over board cells.

Why a dedicated module: belief tracking is mathematically independent
of game logic. Keeping it separate makes it testable in isolation and
allows the strategy module to query it without importing game internals.

Update rules (applied each turn in order):
  1. Direct observation → certainty at observed cell, 0 everywhere else.
  2. No observation → diffusion kernel spreads probability to neighbours.
  3. Barrier mask → cells with barriers zeroed out.
  4. Own-position mask → agent cannot be where we are.
  5. Normalise so all probabilities sum to 1.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

__all__ = ["BeliefState"]

log = logging.getLogger(__name__)


class BeliefState:
    """Uniform-initialised probability map over all grid cells.

    Args:
        rows: Board row count.
        cols: Board column count.
    """

    def __init__(self, rows: int, cols: int) -> None:
        self._rows = rows
        self._cols = cols
        n = rows * cols
        self._prob: dict[tuple[int, int], float] = {
            (x, y): 1.0 / n for y in range(rows) for x in range(cols)
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(
        self,
        own_pos: tuple[int, int],
        opponent_visible: bool,
        opponent_pos: tuple[int, int] | None,
        known_barriers: frozenset[tuple[int, int]],
    ) -> None:
        """Apply one turn of evidence to the belief distribution.

        Args:
            own_pos: This agent's position (opponent cannot be here).
            opponent_visible: Whether the opponent was observed this turn.
            opponent_pos: Observed position when visible; None otherwise.
            known_barriers: Cells with barriers (opponent cannot be there).
        """
        if opponent_visible and opponent_pos is not None:
            self._set_certain(opponent_pos)
        else:
            self._diffuse(known_barriers)
            self._apply_mask(known_barriers)
            self._apply_mask({own_pos})

        self._normalise()
        log.debug(
            "BeliefState updated (visible=%s peak=%.3f @ %s)",
            opponent_visible,
            max(self._prob.values()),
            self.most_likely_pos(),
        )

    def most_likely_pos(self) -> tuple[int, int]:
        """Return the cell with the highest probability."""
        return max(self._prob, key=lambda c: self._prob[c])

    def probability_map(self) -> dict[tuple[int, int], float]:
        """Return a copy of the full probability distribution."""
        return dict(self._prob)

    def summary(self) -> str:
        """Short human-readable summary for prompt injection."""
        peak = self.most_likely_pos()
        prob = self._prob[peak]
        return (
            f"Most likely at column {peak[0]}, row {peak[1]} "
            f"(confidence {prob:.0%})"
        )

    # ------------------------------------------------------------------
    # Private update helpers
    # ------------------------------------------------------------------

    def _set_certain(self, pos: tuple[int, int]) -> None:
        """Set probability to 1.0 at *pos*, 0.0 everywhere else."""
        for cell in self._prob:
            self._prob[cell] = 0.0
        self._prob[pos] = 1.0

    def _diffuse(self, barriers: frozenset[tuple[int, int]]) -> None:
        """Spread probability uniformly to passable neighbours."""
        new: dict[tuple[int, int], float] = dict.fromkeys(self._prob, 0.0)
        for (x, y), p in self._prob.items():
            if p == 0.0:
                continue
            neighbours = list(self._passable_neighbours(x, y, barriers))
            if not neighbours:
                new[(x, y)] += p
                continue
            share = p / (len(neighbours) + 1)
            new[(x, y)] += share
            for nb in neighbours:
                new[nb] += share
        self._prob = new

    def _apply_mask(self, positions: frozenset[tuple[int, int]] | set) -> None:
        """Zero out probability for cells in *positions*."""
        for pos in positions:
            if pos in self._prob:
                self._prob[pos] = 0.0

    def _normalise(self) -> None:
        """Scale probabilities so they sum to 1."""
        total = sum(self._prob.values())
        if total > 0:
            for cell in self._prob:
                self._prob[cell] /= total

    def _passable_neighbours(
        self, x: int, y: int, barriers: frozenset[tuple[int, int]]
    ) -> Iterator[tuple[int, int]]:
        """Yield grid-adjacent cells that are in-bounds and not barriers."""
        for dx, dy in (
            (0, -1), (0, 1), (1, 0), (-1, 0),
            (1, -1), (1, 1), (-1, -1), (-1, 1),
        ):
            nx, ny = x + dx, y + dy
            if (
                0 <= nx < self._cols
                and 0 <= ny < self._rows
                and (nx, ny) not in barriers
            ):
                yield (nx, ny)
