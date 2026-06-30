"""Single sub-game runner.

Why separate from full_game: sub_game owns one episode's lifecycle (state
init, turn loop, result production). full_game owns the series (6 valid
episodes, reruns on failure, final report trigger).
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from src.game.actions import AgentAction
from src.game.barriers import BarrierManager
from src.game.board import Board
from src.game.exceptions import TechnicalFailureError
from src.game.fog_of_war import apply_fog
from src.game.game_state import GameState
from src.game.observed_state import ObservedState
from src.game.scorer import Scorer, SubGameResult
from src.game.turn_manager import TurnManager, TurnOutcome

__all__ = ["SubGame"]

log = logging.getLogger(__name__)

# Signature: (ObservedState, received_message | None) → AgentAction
AgentFn = Callable[[ObservedState, str | None], AgentAction]


class SubGame:
    """Runs one sub-game episode and returns a SubGameResult.

    Args:
        config: Full game config dict.
        game_id: 1-based identifier for this episode.
        scorer: Shared Scorer instance.
    """

    def __init__(self, config: dict, game_id: int, scorer: Scorer) -> None:
        self._cfg = config
        self._game_id = game_id
        self._scorer = scorer

    def run(self, cop_fn: AgentFn, thief_fn: AgentFn) -> SubGameResult:
        """Execute the sub-game loop and return the result.

        Raises:
            TechnicalFailureError: if an agent raises an unexpected exception.
        """
        board = Board(self._cfg["grid_size"])
        barrier_mgr = BarrierManager(self._cfg["max_barriers"])
        state = self._initial_state(barrier_mgr)
        tm = TurnManager(state, board, barrier_mgr, self._cfg["max_moves"])
        messages_exchanged = 0
        radius = self._cfg["visibility_radius"]

        log.info("Sub-game %d starting.", self._game_id)
        outcome = TurnOutcome.ONGOING

        while outcome == TurnOutcome.ONGOING:
            cop_obs = apply_fog(tm.state, "cop", radius)
            thief_obs = apply_fog(tm.state, "thief", radius)
            try:
                thief_action = thief_fn(thief_obs, None)
                cop_action = cop_fn(cop_obs, None)
            except Exception as exc:
                raise TechnicalFailureError(
                    f"Agent raised exception on sub-game {self._game_id}: {exc}"
                ) from exc

            messages_exchanged += 2  # one send per agent per turn
            outcome = tm.step(thief_action, cop_action)

        winner = "cop" if outcome == TurnOutcome.COP_WINS else "thief"
        return self._scorer.compute(
            game_id=self._game_id,
            winner=winner,
            moves=tm.state.move_count,
            barriers_placed=barrier_mgr.count,
            messages_exchanged=messages_exchanged,
            technical_failures=0,
        )

    def _initial_state(self, barrier_mgr: BarrierManager) -> GameState:
        """Build the starting GameState from config."""
        barrier_mgr.reset()
        return GameState(
            cop_pos=tuple(self._cfg["cop_start"]),  # type: ignore[arg-type]
            thief_pos=tuple(self._cfg["thief_start"]),  # type: ignore[arg-type]
            barriers=frozenset(),
            move_count=0,
            barriers_placed=0,
            max_barriers=self._cfg["max_barriers"],
            grid_size=tuple(self._cfg["grid_size"]),  # type: ignore[arg-type]
        )
