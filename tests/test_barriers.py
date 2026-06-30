"""Tests for src.game.barriers."""

from __future__ import annotations

import pytest

from src.game.barriers import BarrierManager


@pytest.fixture
def mgr():
    return BarrierManager(max_barriers=5)


def test_initial_state(mgr):
    assert mgr.count == 0
    assert mgr.remaining == 5
    assert mgr.can_place() is True
    assert mgr.barriers == frozenset()


def test_place_success(mgr):
    result = mgr.place((1, 1))
    assert result is True
    assert mgr.count == 1
    assert (1, 1) in mgr.barriers


def test_place_multiple(mgr):
    for i in range(5):
        assert mgr.place((i, 0)) is True
    assert mgr.count == 5


def test_place_at_cap_rejected(mgr):
    for i in range(5):
        mgr.place((i, 0))
    result = mgr.place((0, 1))  # 6th placement
    assert result is False
    assert mgr.count == 5


def test_place_duplicate_rejected(mgr):
    mgr.place((2, 2))
    result = mgr.place((2, 2))
    assert result is False
    assert mgr.count == 1


def test_can_place_false_at_cap(mgr):
    for i in range(5):
        mgr.place((i, 0))
    assert mgr.can_place() is False


def test_remaining_decrements(mgr):
    mgr.place((0, 0))
    mgr.place((1, 0))
    assert mgr.remaining == 3


def test_reset_clears_all(mgr):
    for i in range(3):
        mgr.place((i, 0))
    mgr.reset()
    assert mgr.count == 0
    assert mgr.barriers == frozenset()
    assert mgr.can_place() is True


def test_barriers_immutable(mgr):
    mgr.place((0, 0))
    b = mgr.barriers
    assert isinstance(b, frozenset)
