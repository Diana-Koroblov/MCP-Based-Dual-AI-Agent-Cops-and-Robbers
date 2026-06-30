"""Full ground-truth game state (never exposed directly to agents).

Why frozen: immutability guarantees that state cannot be silently mutated
inside a callback. Every state transition produces a new GameState object,
making the history trivially reconstructable.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["GameState"]


@dataclass(frozen=True)
class GameState:
    """Complete, ground-truth snapshot of a single game turn.

    This object is INTERNAL to the game engine. It must never be passed
    directly to agents — use ObservedState (filtered by fog_of_war.py) instead.

    Attributes:
        cop_pos: Current Cop position as (x, y).
        thief_pos: Current Thief position as (x, y).
        barriers: Immutable set of all barrier positions.
        move_count: Number of full turns completed so far.
        barriers_placed: Number of barriers the Cop has placed this sub-game.
        max_barriers: Maximum barriers allowed (from config).
        grid_size: (width, height) of the board.
    """

    cop_pos: tuple[int, int]
    thief_pos: tuple[int, int]
    barriers: frozenset[tuple[int, int]]
    move_count: int
    barriers_placed: int
    max_barriers: int
    grid_size: tuple[int, int]

    def with_cop_pos(self, new_pos: tuple[int, int]) -> GameState:
        """Return a new GameState with the Cop at *new_pos*."""
        return GameState(
            cop_pos=new_pos,
            thief_pos=self.thief_pos,
            barriers=self.barriers,
            move_count=self.move_count,
            barriers_placed=self.barriers_placed,
            max_barriers=self.max_barriers,
            grid_size=self.grid_size,
        )

    def with_thief_pos(self, new_pos: tuple[int, int]) -> GameState:
        """Return a new GameState with the Thief at *new_pos*."""
        return GameState(
            cop_pos=self.cop_pos,
            thief_pos=new_pos,
            barriers=self.barriers,
            move_count=self.move_count,
            barriers_placed=self.barriers_placed,
            max_barriers=self.max_barriers,
            grid_size=self.grid_size,
        )

    def with_barrier(self, pos: tuple[int, int]) -> GameState:
        """Return a new GameState with a barrier added at *pos*."""
        return GameState(
            cop_pos=self.cop_pos,
            thief_pos=self.thief_pos,
            barriers=self.barriers | {pos},
            move_count=self.move_count,
            barriers_placed=self.barriers_placed + 1,
            max_barriers=self.max_barriers,
            grid_size=self.grid_size,
        )

    def next_turn(self) -> GameState:
        """Return a new GameState with move_count incremented by 1."""
        return GameState(
            cop_pos=self.cop_pos,
            thief_pos=self.thief_pos,
            barriers=self.barriers,
            move_count=self.move_count + 1,
            barriers_placed=self.barriers_placed,
            max_barriers=self.max_barriers,
            grid_size=self.grid_size,
        )
