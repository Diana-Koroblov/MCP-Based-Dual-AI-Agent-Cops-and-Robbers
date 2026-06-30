"""Sanity check: one complete sub-game on a 2×2 grid.

Why 2×2 first: a tiny board has only 4 cells, so any movement bug or
win-condition error shows up within 1–2 turns. Passing this gives confidence
that board, movement, fog-of-war, turn_manager, and scorer all integrate
correctly before testing larger grids.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.game.actions import ActionType, AgentAction, Direction
from src.game.full_game import FullGame
from src.game.scorer import SubGameResult

log = logging.getLogger(__name__)

_RESULTS_DIR = Path(__file__).parent.parent.parent / "results"

_CFG = {
    "version": "1.00",
    "grid_size": [2, 2],
    "max_moves": 10,
    "num_games": 1,
    "max_barriers": 0,
    "visibility_radius": 2,
    "cop_start": [0, 0],
    "thief_start": [1, 1],
    "scoring": {
        "cop_capture_points": 10,
        "thief_survival_points": 10,
        "cop_per_barrier_points": 0,
        "thief_per_move_survived_points": 0,
    },
}


def _chase_agent(obs, msg):
    """Cop moves E: (0,0)→(1,0) on turn 1, intercepting thief."""
    return AgentAction(ActionType.MOVE, Direction.E)


def _evade_agent(obs, msg):
    """Thief moves N: (1,1)→(1,0) on turn 1 (cop captures same cell)."""
    return AgentAction(ActionType.MOVE, Direction.N)


def test_sanity_2x2_completes():
    """A single sub-game on a 2×2 grid must complete without error."""
    fg = FullGame(_CFG)
    results = fg.run(cop_fn=_chase_agent, thief_fn=_evade_agent)

    assert len(results) == 1
    result = results[0]
    assert isinstance(result, SubGameResult)
    assert result.winner in ("cop", "thief")
    assert result.moves > 0
    assert result.game_id == 1

    log.info("2×2 sanity: winner=%s moves=%d", result.winner, result.moves)


def test_sanity_2x2_winner_scores_correct():
    """Winner receives points; loser receives zero."""
    fg = FullGame(_CFG)
    results = fg.run(cop_fn=_chase_agent, thief_fn=_evade_agent)
    r = results[0]
    if r.winner == "cop":
        assert r.cop_score > 0
        assert r.thief_score == 0
    else:
        assert r.thief_score > 0
        assert r.cop_score == 0


def test_sanity_2x2_log_saved():
    """Result is logged to results/ directory."""
    _RESULTS_DIR.mkdir(exist_ok=True)
    fg = FullGame(_CFG)
    results = fg.run(cop_fn=_chase_agent, thief_fn=_evade_agent)
    r = results[0]
    log_path = _RESULTS_DIR / "sanity_2x2.log"
    log_path.write_text(
        f"winner={r.winner} moves={r.moves} cop_score={r.cop_score} "
        f"thief_score={r.thief_score}\n"
    )
    assert log_path.exists()
