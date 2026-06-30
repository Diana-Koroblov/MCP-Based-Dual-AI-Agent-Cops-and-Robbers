"""Tests for src.game.board."""

from __future__ import annotations

import pytest

from src.game.board import Board


@pytest.fixture
def board():
    return Board([5, 5])


def test_in_bounds_center(board):
    assert board.in_bounds((2, 2)) is True


def test_in_bounds_corners(board):
    assert board.in_bounds((0, 0)) is True
    assert board.in_bounds((4, 4)) is True


def test_out_of_bounds_negative(board):
    assert board.in_bounds((-1, 0)) is False
    assert board.in_bounds((0, -1)) is False


def test_out_of_bounds_too_large(board):
    assert board.in_bounds((5, 0)) is False
    assert board.in_bounds((0, 5)) is False


def test_is_passable_empty(board):
    assert board.is_passable((1, 1), frozenset()) is True


def test_is_passable_barrier_blocks(board):
    barriers = frozenset([(2, 2)])
    assert board.is_passable((2, 2), barriers) is False


def test_is_passable_out_of_bounds(board):
    assert board.is_passable((10, 10), frozenset()) is False


def test_all_cells_count(board):
    cells = board.all_cells()
    assert len(cells) == 25  # 5x5


def test_all_cells_no_duplicates(board):
    cells = board.all_cells()
    assert len(cells) == len(set(cells))


def test_board_non_square():
    b = Board([3, 4])
    assert b.width == 3
    assert b.height == 4
    assert len(b.all_cells()) == 12


def test_repr(board):
    assert "5" in repr(board)
