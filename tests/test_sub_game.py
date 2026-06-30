"""Tests for src.game.sub_game."""

from __future__ import annotations

import pytest

from src.game.actions import ActionType, AgentAction, Direction
from src.game.exceptions import TechnicalFailureError
from src.game.observed_state import ObservedState
from src.game.scorer import Scorer, SubGameResult
from src.game.sub_game import SubGame


@pytest.fixture
def scoring_cfg():
    return {"cop_capture_points": 10, "thief_survival_points": 10,
            "cop_per_barrier_points": 1, "thief_per_move_survived_points": 0}


@pytest.fixture
def cfg(scoring_cfg):
    return {
        "grid_size": [5, 5], "max_moves": 25, "max_barriers": 5,
        "visibility_radius": 2, "cop_start": [0, 0], "thief_start": [4, 4],
        "scoring": scoring_cfg,
    }


def _always_move(direction: Direction):
    """Return an agent fn that always moves in *direction*, ignoring observations."""
    action = AgentAction(ActionType.MOVE, direction)
    return lambda obs, msg: action


# ---------------------------------------------------------------------------
# Happy path — thief survives (cop moves away from thief)
# ---------------------------------------------------------------------------

def test_thief_wins_survival(cfg):
    # Cap moves at 4 so neither agent walks off the edge of the 5x5 board.
    # Cop (0,0) moves E×4 → (4,0); thief (4,4) moves W×4 → (0,4) — no capture.
    cfg = {**cfg, "max_moves": 4}
    scorer = Scorer(cfg["scoring"])
    sg = SubGame(cfg, game_id=1, scorer=scorer)
    result = sg.run(
        cop_fn=_always_move(Direction.E),
        thief_fn=_always_move(Direction.W),
    )
    assert isinstance(result, SubGameResult)
    assert result.winner == "thief"
    assert result.game_id == 1
    assert result.moves == 4


# ---------------------------------------------------------------------------
# Happy path — cop wins (small 2x2 board, quick capture)
# ---------------------------------------------------------------------------

def test_cop_wins_small_board():
    small_cfg = {
        "grid_size": [2, 2], "max_moves": 10, "max_barriers": 0,
        "visibility_radius": 2, "cop_start": [0, 0], "thief_start": [1, 1],
        "scoring": {"cop_capture_points": 10, "thief_survival_points": 10,
                    "cop_per_barrier_points": 0, "thief_per_move_survived_points": 0},
    }
    scorer = Scorer(small_cfg["scoring"])
    sg = SubGame(small_cfg, game_id=1, scorer=scorer)
    # Thief (1,1) moves N→(1,0); cop (0,0) moves E→(1,0) — capture on turn 1.
    result = sg.run(
        cop_fn=_always_move(Direction.E),
        thief_fn=_always_move(Direction.N),
    )
    assert result.winner == "cop"


# ---------------------------------------------------------------------------
# Technical failure path
# ---------------------------------------------------------------------------

def test_technical_failure_propagated(cfg):
    scorer = Scorer(cfg["scoring"])
    sg = SubGame(cfg, game_id=2, scorer=scorer)

    def crashing_agent(obs: ObservedState, msg):
        raise RuntimeError("LLM timeout")

    with pytest.raises(TechnicalFailureError, match="LLM timeout"):
        sg.run(cop_fn=crashing_agent, thief_fn=_always_move(Direction.N))


# ---------------------------------------------------------------------------
# Result fields
# ---------------------------------------------------------------------------

def test_result_messages_exchanged(cfg):
    # Cap at 4 moves so agents don't walk off the board.
    # cop (0,0)→E×4; thief (4,4)→W×4 — no capture, thief wins.
    cfg = {**cfg, "max_moves": 4}
    scorer = Scorer(cfg["scoring"])
    sg = SubGame(cfg, game_id=3, scorer=scorer)
    result = sg.run(
        cop_fn=_always_move(Direction.E),
        thief_fn=_always_move(Direction.W),
    )
    # 2 messages per turn (one per agent)
    assert result.messages_exchanged == result.moves * 2
