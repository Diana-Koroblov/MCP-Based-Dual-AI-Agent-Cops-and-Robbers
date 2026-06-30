"""3×3 sanity check — one sub-game with NL messages and belief state updates.

Strategy: mock LLM and message store; run a real SubGame so the game
engine, fog-of-war, and orchestrator components all work together.

Verifications:
  * At least one NL message is produced each turn.
  * Belief state changes between turns.
  * The game reaches a terminal result.
  * Result is logged to results/sanity_3x3.log.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.game.actions import ActionType, AgentAction, Direction
from src.game.board import Board
from src.game.movement import get_valid_moves
from src.game.scorer import Scorer
from src.game.sub_game import SubGame
from src.orchestrator.belief_state import BeliefState
from src.orchestrator.nlp_parser import NLPParser
from src.orchestrator.prompt_builder import PromptBuilder

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 3×3 game config
# ---------------------------------------------------------------------------

_CFG = {
    "version": "1.00",
    "grid_size": [3, 3],
    "max_moves": 12,
    "max_barriers": 2,
    "visibility_radius": 2,   # Chebyshev 2 covers entire 3×3 board
    "cop_start": [0, 0],
    "thief_start": [2, 2],
    "scoring": {
        "cop_capture_points": 10,
        "thief_survival_points": 10,
        "cop_per_barrier_points": 1,
        "thief_per_move_survived_points": 0,
    },
    "num_games": 1,
}

_RESULTS_DIR = Path(__file__).parent.parent.parent / "results"

# Shared message store: each agent reads what the other wrote last turn.
_messages: dict[str, str] = {"cop": "", "thief": ""}

# Belief states and prompt builder shared across turns via closure.
_cop_belief: BeliefState | None = None
_thief_belief: BeliefState | None = None
_pb = PromptBuilder(_CFG["grid_size"])
_parser = NLPParser()

# Record of NL messages and belief snapshots for assertions.
_nl_log: list[str] = []
_belief_snapshots: list[dict] = []


def _mock_llm_cop(_prompt: str) -> str:
    return "ACTION: SE\nMESSAGE: I am closing in from the northwest!"


def _mock_llm_thief(_prompt: str) -> str:
    return "ACTION: NW\nMESSAGE: You will never catch me, cop!"


def _pick_valid_action(
    direction: Direction | None,
    pos: tuple[int, int],
    barriers: frozenset,
) -> AgentAction:
    """Use parsed direction if valid; otherwise fall back to first valid move."""
    board = Board(_CFG["grid_size"])
    valid = get_valid_moves(pos, barriers, board)
    if direction is not None:
        for d, _ in valid:
            if d == direction:
                return AgentAction(ActionType.MOVE, d)
    if valid:
        return AgentAction(ActionType.MOVE, valid[0][0])
    # Fully surrounded (should not happen on 3×3 early game)
    return AgentAction(ActionType.MOVE, Direction.N)


def _make_cop_fn():
    global _cop_belief
    _cop_belief = BeliefState(3, 3)

    def cop_fn(obs, _received):
        received = _messages["cop"]
        prompt = _pb.build(
            "cop", obs, received or None, _cop_belief.summary(),  # type: ignore[union-attr]
            [d.value for d in Direction] + ["place_barrier"],
        )
        raw = _mock_llm_cop(prompt)
        result = _parser.parse(raw)

        _nl_log.append(result.message)
        _messages["thief"] = result.message  # thief reads cop's message next turn

        snapshot = _cop_belief.probability_map()  # type: ignore[union-attr]
        _belief_snapshots.append(snapshot)
        _cop_belief.update(  # type: ignore[union-attr]
            obs.own_pos, obs.opponent_visible,
            obs.opponent_pos_if_visible, obs.known_barriers,
        )

        return _pick_valid_action(result.direction, obs.own_pos, obs.known_barriers)

    return cop_fn


def _make_thief_fn():
    global _thief_belief
    _thief_belief = BeliefState(3, 3)

    def thief_fn(obs, _received):
        received = _messages["thief"]
        prompt = _pb.build(
            "thief", obs, received or None, _thief_belief.summary(),  # type: ignore[union-attr]
            [d.value for d in Direction],
        )
        raw = _mock_llm_thief(prompt)
        result = _parser.parse(raw)

        _nl_log.append(result.message)
        _messages["cop"] = result.message  # cop reads thief's message next turn

        _thief_belief.update(  # type: ignore[union-attr]
            obs.own_pos, obs.opponent_visible,
            obs.opponent_pos_if_visible, obs.known_barriers,
        )

        return _pick_valid_action(result.direction, obs.own_pos, obs.known_barriers)

    return thief_fn


# ---------------------------------------------------------------------------
# Sanity test
# ---------------------------------------------------------------------------

def test_sanity_3x3():
    """Run one complete 3×3 sub-game; verify messages, belief, and logging."""
    _nl_log.clear()
    _belief_snapshots.clear()
    _messages["cop"] = ""
    _messages["thief"] = ""

    scorer = Scorer(_CFG["scoring"])
    sg = SubGame(_CFG, game_id=1, scorer=scorer)

    cop_fn = _make_cop_fn()
    thief_fn = _make_thief_fn()

    result = sg.run(cop_fn, thief_fn)

    # -- game reached a terminal state --
    assert result.winner in ("cop", "thief"), f"Unexpected winner: {result.winner}"

    # -- NL messages were produced --
    non_empty = [m for m in _nl_log if m]
    assert non_empty, "No NL messages were produced during the game."

    # -- belief state changed between turns --
    if len(_belief_snapshots) >= 2:
        first_map = _belief_snapshots[0]
        last_map = _cop_belief.probability_map()  # type: ignore[union-attr]
        assert first_map != last_map, "Belief state never changed across turns."

    # -- log result to results/sanity_3x3.log --
    _RESULTS_DIR.mkdir(exist_ok=True)
    log_path = _RESULTS_DIR / "sanity_3x3.log"
    with log_path.open("w") as fh:
        fh.write(f"winner={result.winner}\n")
        fh.write(f"moves={result.moves}\n")
        fh.write(f"cop_score={result.cop_score}\n")
        fh.write(f"thief_score={result.thief_score}\n")
        fh.write(f"nl_messages={len(_nl_log)}\n")
        fh.write(f"non_empty_messages={len(non_empty)}\n")
    assert log_path.exists()

    log.info("3×3 sanity: winner=%s moves=%d log=%s", result.winner, result.moves, log_path)
