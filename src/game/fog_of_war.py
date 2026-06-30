"""Fog-of-war filter: GameState → ObservedState.

Why Chebyshev distance (not Euclidean): Chebyshev is consistent with
8-directional movement — the "radius" is the number of king-moves away.
An agent at (0,0) with radius 2 can see exactly the cells it could reach
in 2 moves, which is the most intuitive definition for this game.
"""

from __future__ import annotations

import logging

from src.game.game_state import GameState
from src.game.observed_state import ObservedState

__all__ = ["apply_fog", "chebyshev_distance"]

log = logging.getLogger(__name__)


def chebyshev_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Return the Chebyshev (chessboard) distance between cells *a* and *b*.

    Chebyshev distance = max(|Δx|, |Δy|), which equals the minimum number
    of king-moves required to travel from *a* to *b* on an infinite board.
    """
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def apply_fog(
    state: GameState,
    for_agent: str,
    visibility_radius: int,
) -> ObservedState:
    """Filter *state* through the fog-of-war lens for *for_agent*.

    Args:
        state: Full ground-truth game state.
        for_agent: Either 'cop' or 'thief'.
        visibility_radius: Chebyshev radius within which the opponent is visible.

    Returns:
        An ObservedState that hides the opponent if they are beyond the radius.

    Raises:
        ValueError: if *for_agent* is not 'cop' or 'thief'.
    """
    if for_agent == "cop":
        own_pos = state.cop_pos
        opp_pos = state.thief_pos
        barriers_remaining = state.max_barriers - state.barriers_placed
    elif for_agent == "thief":
        own_pos = state.thief_pos
        opp_pos = state.cop_pos
        barriers_remaining = 0  # Thief never places barriers
    else:
        raise ValueError(f"for_agent must be 'cop' or 'thief', got '{for_agent}'")

    dist = chebyshev_distance(own_pos, opp_pos)
    opponent_visible = dist <= visibility_radius

    log.debug(
        "Fog [%s]: own=%s opp=%s dist=%d radius=%d visible=%s",
        for_agent, own_pos, opp_pos, dist, visibility_radius, opponent_visible,
    )

    return ObservedState(
        own_pos=own_pos,
        known_barriers=state.barriers,
        opponent_visible=opponent_visible,
        opponent_pos_if_visible=opp_pos if opponent_visible else None,
        move_count=state.move_count,
        barriers_remaining=barriers_remaining,
    )
