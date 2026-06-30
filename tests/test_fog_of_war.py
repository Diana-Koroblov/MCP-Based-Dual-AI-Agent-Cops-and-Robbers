"""Tests for src.game.fog_of_war."""

from __future__ import annotations

import pytest

from src.game.fog_of_war import apply_fog, chebyshev_distance
from src.game.game_state import GameState


@pytest.fixture
def base_state():
    return GameState(
        cop_pos=(0, 0),
        thief_pos=(4, 4),
        barriers=frozenset(),
        move_count=0,
        barriers_placed=0,
        max_barriers=5,
        grid_size=(5, 5),
    )


# ---------------------------------------------------------------------------
# chebyshev_distance
# ---------------------------------------------------------------------------

def test_chebyshev_same_cell():
    assert chebyshev_distance((2, 2), (2, 2)) == 0


def test_chebyshev_adjacent():
    assert chebyshev_distance((0, 0), (1, 1)) == 1


def test_chebyshev_diagonal():
    assert chebyshev_distance((0, 0), (3, 2)) == 3


def test_chebyshev_horizontal():
    assert chebyshev_distance((0, 0), (4, 0)) == 4


# ---------------------------------------------------------------------------
# apply_fog — opponent NOT visible (far away)
# ---------------------------------------------------------------------------

def test_fog_cop_opponent_not_visible(base_state):
    obs = apply_fog(base_state, "cop", visibility_radius=2)
    # cop=(0,0), thief=(4,4) → chebyshev dist=4 > 2 → not visible
    assert obs.opponent_visible is False
    assert obs.opponent_pos_if_visible is None
    assert obs.own_pos == (0, 0)


def test_fog_thief_opponent_not_visible(base_state):
    obs = apply_fog(base_state, "thief", visibility_radius=2)
    assert obs.opponent_visible is False
    assert obs.own_pos == (4, 4)
    assert obs.barriers_remaining == 0  # thief never has barriers


# ---------------------------------------------------------------------------
# apply_fog — opponent IS visible (nearby)
# ---------------------------------------------------------------------------

def test_fog_cop_sees_thief_when_adjacent():
    state = GameState(
        cop_pos=(2, 2), thief_pos=(3, 3),
        barriers=frozenset(), move_count=5,
        barriers_placed=2, max_barriers=5, grid_size=(5, 5),
    )
    obs = apply_fog(state, "cop", visibility_radius=2)
    assert obs.opponent_visible is True
    assert obs.opponent_pos_if_visible == (3, 3)
    assert obs.barriers_remaining == 3  # 5 - 2


def test_fog_radius_boundary_exactly():
    state = GameState(
        cop_pos=(0, 0), thief_pos=(2, 0),
        barriers=frozenset(), move_count=0,
        barriers_placed=0, max_barriers=5, grid_size=(5, 5),
    )
    # dist=2, radius=2 → exactly on boundary → visible
    obs = apply_fog(state, "cop", visibility_radius=2)
    assert obs.opponent_visible is True


def test_fog_radius_just_outside():
    state = GameState(
        cop_pos=(0, 0), thief_pos=(3, 0),
        barriers=frozenset(), move_count=0,
        barriers_placed=0, max_barriers=5, grid_size=(5, 5),
    )
    obs = apply_fog(state, "cop", visibility_radius=2)
    assert obs.opponent_visible is False


# ---------------------------------------------------------------------------
# Barriers always visible; move_count passed through
# ---------------------------------------------------------------------------

def test_fog_barriers_always_included():
    barriers = frozenset([(1, 1), (2, 2)])
    state = GameState(
        cop_pos=(0, 0), thief_pos=(4, 4),
        barriers=barriers, move_count=3,
        barriers_placed=2, max_barriers=5, grid_size=(5, 5),
    )
    obs = apply_fog(state, "cop", visibility_radius=2)
    assert obs.known_barriers == barriers
    assert obs.move_count == 3


def test_fog_invalid_agent_raises(base_state):
    with pytest.raises(ValueError, match="cop.*thief"):
        apply_fog(base_state, "robot", visibility_radius=2)
