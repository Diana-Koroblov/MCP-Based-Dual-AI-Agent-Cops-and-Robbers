"""Tests for src.game.movement."""

from __future__ import annotations

import pytest

from src.game.actions import ActionType, AgentAction, Direction
from src.game.board import Board
from src.game.exceptions import InvalidActionError
from src.game.movement import apply_direction, get_valid_moves, resolve_move


@pytest.fixture
def board():
    return Board([5, 5])


# ---------------------------------------------------------------------------
# apply_direction
# ---------------------------------------------------------------------------

def test_apply_direction_north():
    assert apply_direction((2, 2), Direction.N) == (2, 1)


def test_apply_direction_southeast():
    assert apply_direction((2, 2), Direction.SE) == (3, 3)


def test_apply_direction_all_eight():
    pos = (2, 2)
    results = {d: apply_direction(pos, d) for d in Direction}
    assert len(set(results.values())) == 8  # all 8 destinations are distinct


# ---------------------------------------------------------------------------
# get_valid_moves
# ---------------------------------------------------------------------------

def test_get_valid_moves_center_no_barriers(board):
    moves = get_valid_moves((2, 2), frozenset(), board)
    assert len(moves) == 8


def test_get_valid_moves_corner_limited(board):
    moves = get_valid_moves((0, 0), frozenset(), board)
    # From (0,0) only SE, S, E are in-bounds
    assert len(moves) == 3


def test_get_valid_moves_barrier_excluded(board):
    barriers = frozenset([(2, 1)])  # North of (2,2)
    moves = get_valid_moves((2, 2), barriers, board)
    directions = [d for d, _ in moves]
    assert Direction.N not in directions       # (2,1) is the barrier — N blocked
    assert Direction.NE in directions          # (3,1) is not a barrier — NE valid
    # Double-check N is blocked
    assert Direction.N not in directions


def test_get_valid_moves_returns_correct_positions(board):
    moves = get_valid_moves((0, 0), frozenset(), board)
    positions = [pos for _, pos in moves]
    assert (1, 0) in positions  # E
    assert (0, 1) in positions  # S
    assert (1, 1) in positions  # SE


# ---------------------------------------------------------------------------
# resolve_move
# ---------------------------------------------------------------------------

def test_resolve_move_valid(board):
    action = AgentAction(ActionType.MOVE, Direction.E)
    new_pos = resolve_move((2, 2), action, frozenset(), board)
    assert new_pos == (3, 2)


def test_resolve_move_into_barrier_raises(board):
    barriers = frozenset([(3, 2)])
    action = AgentAction(ActionType.MOVE, Direction.E)
    with pytest.raises(InvalidActionError):
        resolve_move((2, 2), action, barriers, board)


def test_resolve_move_out_of_bounds_raises(board):
    action = AgentAction(ActionType.MOVE, Direction.N)
    with pytest.raises(InvalidActionError):
        resolve_move((0, 0), action, frozenset(), board)


def test_resolve_move_wrong_action_type_raises(board):
    action = AgentAction(ActionType.PLACE_BARRIER)
    with pytest.raises(InvalidActionError):
        resolve_move((2, 2), action, frozenset(), board)
