"""Tests for BeliefState — probability distribution over board cells.

Covers:
  * Initial uniform distribution.
  * Direct observation sets certainty to 1.0.
  * Fog-of-war (no observation) triggers diffusion and masks.
  * Barrier mask zeros excluded cells.
  * own_pos mask zeros the agent's own cell.
  * most_likely_pos() and probability_map() correctness.
  * summary() string format.
"""

from __future__ import annotations

import pytest

from src.orchestrator.belief_state import BeliefState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uniform_3x3() -> BeliefState:
    return BeliefState(rows=3, cols=3)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def test_initial_distribution_is_uniform():
    bs = _uniform_3x3()
    probs = list(bs.probability_map().values())
    expected = 1.0 / 9
    assert all(abs(p - expected) < 1e-9 for p in probs)


def test_initial_all_cells_covered():
    bs = _uniform_3x3()
    assert len(bs.probability_map()) == 9


def test_initial_probabilities_sum_to_one():
    bs = _uniform_3x3()
    total = sum(bs.probability_map().values())
    assert abs(total - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# Direct observation → certainty
# ---------------------------------------------------------------------------

def test_direct_observation_sets_certainty():
    bs = _uniform_3x3()
    bs.update(
        own_pos=(0, 0),
        opponent_visible=True,
        opponent_pos=(2, 2),
        known_barriers=frozenset(),
    )
    pmap = bs.probability_map()
    assert abs(pmap[(2, 2)] - 1.0) < 1e-9


def test_direct_observation_zeros_all_other_cells():
    bs = _uniform_3x3()
    bs.update(
        own_pos=(0, 0),
        opponent_visible=True,
        opponent_pos=(1, 1),
        known_barriers=frozenset(),
    )
    pmap = bs.probability_map()
    for cell, prob in pmap.items():
        if cell != (1, 1):
            assert prob == 0.0, f"Cell {cell} should be 0 but got {prob}"


def test_most_likely_pos_after_certain_observation():
    bs = _uniform_3x3()
    bs.update(own_pos=(0, 0), opponent_visible=True, opponent_pos=(2, 1), known_barriers=frozenset())
    assert bs.most_likely_pos() == (2, 1)


# ---------------------------------------------------------------------------
# Fog-of-war (no observation) → diffusion + masks
# ---------------------------------------------------------------------------

def test_fog_update_still_sums_to_one():
    bs = _uniform_3x3()
    bs.update(
        own_pos=(1, 1),
        opponent_visible=False,
        opponent_pos=None,
        known_barriers=frozenset(),
    )
    total = sum(bs.probability_map().values())
    assert abs(total - 1.0) < 1e-9


def test_fog_own_pos_zeroed():
    bs = _uniform_3x3()
    bs.update(
        own_pos=(1, 1),
        opponent_visible=False,
        opponent_pos=None,
        known_barriers=frozenset(),
    )
    assert bs.probability_map()[(1, 1)] == 0.0


def test_fog_barrier_cells_zeroed():
    bs = _uniform_3x3()
    barriers = frozenset({(0, 0), (1, 0)})
    bs.update(
        own_pos=(2, 2),
        opponent_visible=False,
        opponent_pos=None,
        known_barriers=barriers,
    )
    pmap = bs.probability_map()
    assert pmap[(0, 0)] == 0.0
    assert pmap[(1, 0)] == 0.0


def test_fog_multiple_updates_stay_normalised():
    bs = _uniform_3x3()
    for _ in range(5):
        bs.update(
            own_pos=(0, 0),
            opponent_visible=False,
            opponent_pos=None,
            known_barriers=frozenset(),
        )
    total = sum(bs.probability_map().values())
    assert abs(total - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# most_likely_pos and probability_map
# ---------------------------------------------------------------------------

def test_probability_map_returns_copy():
    bs = _uniform_3x3()
    m1 = bs.probability_map()
    m1[(0, 0)] = 99.0  # mutate the copy
    m2 = bs.probability_map()
    assert m2[(0, 0)] != 99.0  # original unchanged


def test_most_likely_pos_after_fog_excludes_own_pos():
    bs = _uniform_3x3()
    bs.update(own_pos=(1, 1), opponent_visible=False, opponent_pos=None, known_barriers=frozenset())
    assert bs.most_likely_pos() != (1, 1)


# ---------------------------------------------------------------------------
# summary()
# ---------------------------------------------------------------------------

def test_summary_contains_column_and_row():
    bs = _uniform_3x3()
    bs.update(own_pos=(0, 0), opponent_visible=True, opponent_pos=(2, 1), known_barriers=frozenset())
    s = bs.summary()
    assert "column 2" in s
    assert "row 1" in s


def test_summary_contains_confidence():
    bs = _uniform_3x3()
    bs.update(own_pos=(0, 0), opponent_visible=True, opponent_pos=(1, 2), known_barriers=frozenset())
    assert "100%" in bs.summary()
