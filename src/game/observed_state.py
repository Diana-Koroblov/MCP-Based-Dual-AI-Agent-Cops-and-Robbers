"""Partial observation given to each agent (fog-of-war filtered).

Why a separate dataclass from GameState: agents must never receive ground
truth. Having a distinct type makes it a compile-time error to accidentally
pass a GameState where an ObservedState is expected.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["ObservedState"]


@dataclass(frozen=True)
class ObservedState:
    """Partial, agent-visible snapshot produced by fog_of_war.apply_fog().

    Attributes:
        own_pos: This agent's current position.
        known_barriers: All barrier positions (always fully visible).
        opponent_visible: True if the opponent is within visibility_radius.
        opponent_pos_if_visible: Opponent's position when visible; None otherwise.
            Invariant: always None when opponent_visible is False.
        move_count: Number of full turns completed so far.
        barriers_remaining: How many more barriers the Cop may place
            (always 0 for the Thief).
    """

    own_pos: tuple[int, int]
    known_barriers: frozenset[tuple[int, int]]
    opponent_visible: bool
    opponent_pos_if_visible: tuple[int, int] | None
    move_count: int
    barriers_remaining: int

    def __post_init__(self) -> None:
        """Enforce the invariant: opponent_pos_if_visible is None iff not visible."""
        if not self.opponent_visible and self.opponent_pos_if_visible is not None:
            raise ValueError(
                "opponent_pos_if_visible must be None when opponent_visible is False."
            )
        if self.opponent_visible and self.opponent_pos_if_visible is None:
            raise ValueError(
                "opponent_pos_if_visible must be set when opponent_visible is True."
            )
