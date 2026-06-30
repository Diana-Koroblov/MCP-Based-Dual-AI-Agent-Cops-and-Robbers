"""Tests for src.game.scorer."""

from __future__ import annotations

import pytest

from src.game.scorer import Scorer, ScoreSummary, SubGameResult


@pytest.fixture
def scoring_cfg():
    return {
        "cop_capture_points": 10,
        "thief_survival_points": 10,
        "cop_per_barrier_points": 1,
        "thief_per_move_survived_points": 0,
    }


@pytest.fixture
def scorer(scoring_cfg):
    return Scorer(scoring_cfg)


# ---------------------------------------------------------------------------
# compute — cop wins
# ---------------------------------------------------------------------------

def test_cop_win_score(scorer):
    result = scorer.compute(1, "cop", moves=12, barriers_placed=3,
                            messages_exchanged=24, technical_failures=0)
    assert result.winner == "cop"
    assert result.cop_score == 13   # 10 base + 3 barriers
    assert result.thief_score == 0


def test_cop_win_no_barriers(scorer):
    result = scorer.compute(1, "cop", moves=5, barriers_placed=0,
                            messages_exchanged=10, technical_failures=0)
    assert result.cop_score == 10


# ---------------------------------------------------------------------------
# compute — thief wins
# ---------------------------------------------------------------------------

def test_thief_win_score(scorer):
    result = scorer.compute(2, "thief", moves=25, barriers_placed=0,
                            messages_exchanged=50, technical_failures=0)
    assert result.winner == "thief"
    assert result.thief_score == 10
    assert result.cop_score == 0


# ---------------------------------------------------------------------------
# compute — metadata fields
# ---------------------------------------------------------------------------

def test_result_fields(scorer):
    result = scorer.compute(3, "cop", moves=8, barriers_placed=1,
                            messages_exchanged=16, technical_failures=2)
    assert result.game_id == 3
    assert result.moves == 8
    assert result.barriers_placed == 1
    assert result.messages_exchanged == 16
    assert result.technical_failures == 2


# ---------------------------------------------------------------------------
# summarise
# ---------------------------------------------------------------------------

def _make_result(game_id, winner, cop_score, thief_score):
    return SubGameResult(
        game_id=game_id, winner=winner, moves=10,
        cop_score=cop_score, thief_score=thief_score,
        barriers_placed=0, messages_exchanged=20, technical_failures=0,
    )


def test_summarise_totals():
    results = [
        _make_result(1, "cop", 10, 0),
        _make_result(2, "thief", 0, 10),
        _make_result(3, "cop", 11, 0),
    ]
    summary = Scorer.summarise(results)
    assert summary.cop_total_score == 21
    assert summary.thief_total_score == 10
    assert summary.cop_wins == 2
    assert summary.thief_wins == 1


def test_summarise_all_thief_wins():
    results = [_make_result(i, "thief", 0, 10) for i in range(1, 7)]
    summary = Scorer.summarise(results)
    assert summary.cop_wins == 0
    assert summary.thief_wins == 6
    assert isinstance(summary, ScoreSummary)
