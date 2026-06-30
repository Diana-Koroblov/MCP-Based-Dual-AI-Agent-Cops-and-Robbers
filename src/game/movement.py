"""Movement validation and resolution.

Why separate from Board: movement logic (delta application, valid-move listing)
is distinct from the grid's structural knowledge. Keeping them apart makes
each module testable independently.
"""

from __future__ import annotations

import logging

from src.game.actions import DIRECTION_DELTAS, ActionType, AgentAction, Direction
from src.game.board import Board
from src.game.exceptions import InvalidActionError

__all__ = ["apply_direction", "get_valid_moves", "resolve_move"]

log = logging.getLogger(__name__)


def apply_direction(
    pos: tuple[int, int], direction: Direction
) -> tuple[int, int]:
    """Return the cell reached by moving *direction* from *pos*."""
    dx, dy = DIRECTION_DELTAS[direction]
    return (pos[0] + dx, pos[1] + dy)


def get_valid_moves(
    pos: tuple[int, int],
    barriers: frozenset[tuple[int, int]],
    board: Board,
) -> list[tuple[Direction, tuple[int, int]]]:
    """Return all (direction, new_pos) pairs that are passable from *pos*.

    Args:
        pos: Current agent position.
        barriers: Set of impassable barrier cells.
        board: Board instance for bounds checking.

    Returns:
        List of (Direction, destination) tuples. Empty list means the agent
        is fully surrounded — treated as a hold.
    """
    moves = []
    for direction in Direction:
        new_pos = apply_direction(pos, direction)
        if board.is_passable(new_pos, barriers):
            moves.append((direction, new_pos))
    return moves


def resolve_move(
    pos: tuple[int, int],
    action: AgentAction,
    barriers: frozenset[tuple[int, int]],
    board: Board,
) -> tuple[int, int]:
    """Apply a MOVE action and return the new position.

    Raises:
        InvalidActionError: if the action is not a MOVE, or the destination
            is out of bounds or blocked by a barrier.
    """
    if action.action_type != ActionType.MOVE:
        raise InvalidActionError(
            f"resolve_move expects a MOVE action, got {action.action_type}"
        )
    new_pos = apply_direction(pos, action.direction)  # type: ignore[arg-type]
    if not board.is_passable(new_pos, barriers):
        raise InvalidActionError(
            f"Destination {new_pos} is not passable (out-of-bounds or barrier)."
        )
    log.debug("Move resolved: %s -> %s via %s", pos, new_pos, action.direction)
    return new_pos
