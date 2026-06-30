"""Tests for src.game.turn_manager."""

from __future__ import annotations

import pytest

from src.game.actions import ActionType, AgentAction, Direction
from src.game.barriers import BarrierManager
from src.game.board import Board
from src.game.exceptions import InvalidActionError
from src.game.game_state import GameState
from src.game.turn_manager import TurnManager, TurnOutcome


def _make_tm(cop=(0, 0), thief=(4, 4), move_count=0, max_moves=25, barriers=None):
    board = Board([5, 5])
    barrier_mgr = BarrierManager(5)
    state = GameState(
        cop_pos=cop, thief_pos=thief,
        barriers=frozenset(barriers or []),
        move_count=move_count, barriers_placed=0,
        max_barriers=5, grid_size=(5, 5),
    )
    return TurnManager(state, board, barrier_mgr, max_moves)


def _move(direction):
    return AgentAction(ActionType.MOVE, direction)


def _barrier():
    return AgentAction(ActionType.PLACE_BARRIER)


# ---------------------------------------------------------------------------
# ONGOING turns
# ---------------------------------------------------------------------------

def test_step_ongoing(board_5x5):
    tm = _make_tm()
    outcome = tm.step(_move(Direction.W), _move(Direction.E))
    assert outcome == TurnOutcome.ONGOING
    assert tm.state.move_count == 1


def test_thief_position_updated():
    tm = _make_tm(thief=(2, 2))
    tm.step(_move(Direction.N), _move(Direction.E))
    assert tm.state.thief_pos == (2, 1)


def test_cop_position_updated():
    tm = _make_tm(cop=(0, 0))
    # Thief at (4,4) moves W→(3,4); cop at (0,0) moves E→(1,0)
    tm.step(_move(Direction.W), _move(Direction.E))
    assert tm.state.cop_pos == (1, 0)


# ---------------------------------------------------------------------------
# COP_WINS — cop moves onto thief
# ---------------------------------------------------------------------------

def test_cop_wins_capture():
    # thief at (2,2) moves S → (2,3); cop at (3,3) moves W → (2,3) → capture
    tm = _make_tm(cop=(3, 3), thief=(2, 2))
    outcome = tm.step(_move(Direction.S), _move(Direction.W))
    assert outcome == TurnOutcome.COP_WINS


# ---------------------------------------------------------------------------
# THIEF_WINS — survival
# ---------------------------------------------------------------------------

def test_thief_wins_survival():
    tm = _make_tm(max_moves=1)
    outcome = tm.step(_move(Direction.W), _move(Direction.E))
    assert outcome == TurnOutcome.THIEF_WINS


# ---------------------------------------------------------------------------
# Barrier placement
# ---------------------------------------------------------------------------

def test_cop_places_barrier_does_not_move():
    tm = _make_tm(cop=(2, 2))
    # Thief at (4,4) moves W→(3,4) — valid; cop places barrier at (2,2)
    tm.step(_move(Direction.W), _barrier())
    assert tm.state.cop_pos == (2, 2)
    assert (2, 2) in tm.state.barriers


def test_thief_cannot_place_barrier():
    tm = _make_tm()
    with pytest.raises(InvalidActionError):
        tm.step(_barrier(), _move(Direction.E))


# ---------------------------------------------------------------------------
# Edge: cop attempts 6th barrier (cap enforced by BarrierManager)
# ---------------------------------------------------------------------------

def test_sixth_barrier_rejected():
    board = Board([5, 5])
    barrier_mgr = BarrierManager(5)
    for i in range(5):
        barrier_mgr.place((i, 4))  # pre-fill 5 barriers
    state = GameState(
        cop_pos=(0, 0), thief_pos=(4, 4),
        barriers=barrier_mgr.barriers,
        move_count=0, barriers_placed=5,
        max_barriers=5, grid_size=(5, 5),
    )
    tm = TurnManager(state, board, barrier_mgr, 25)
    outcome = tm.step(_move(Direction.N), _barrier())  # thief N from (4,4)→(4,3), not a barrier
    # Barrier rejected → cop stays, no new barrier, game continues
    assert outcome == TurnOutcome.ONGOING
    assert tm.state.cop_pos == (0, 0)
