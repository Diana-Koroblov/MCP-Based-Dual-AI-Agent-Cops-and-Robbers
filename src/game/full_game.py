"""Full 6-sub-game series orchestration.

Why full_game owns reruns: the sub_game raises TechnicalFailureError and
knows nothing about retry logic. Keeping retry logic here means sub_game
stays simple and testable in isolation.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from src.game.actions import AgentAction
from src.game.exceptions import TechnicalFailureError
from src.game.observed_state import ObservedState
from src.game.scorer import Scorer, ScoreSummary, SubGameResult
from src.game.sub_game import SubGame

__all__ = ["FullGame"]

log = logging.getLogger(__name__)

AgentFn = Callable[[ObservedState, str | None], AgentAction]

_MAX_RERUN_ATTEMPTS = 10  # safety cap to prevent infinite loops on persistent failures


class FullGame:
    """Runs exactly *num_games* valid sub-games, re-running on technical failure.

    Args:
        config: Full game config dict.
    """

    def __init__(self, config: dict) -> None:
        self._cfg = config
        self._scorer = Scorer(config["scoring"])

    def run(self, cop_fn: AgentFn, thief_fn: AgentFn) -> list[SubGameResult]:
        """Execute the full series and return exactly *num_games* results.

        Each sub-game is automatically re-run if TechnicalFailureError is raised.
        Raises RuntimeError if a single episode fails more than _MAX_RERUN_ATTEMPTS.
        """
        num_games: int = self._cfg["num_games"]
        results: list[SubGameResult] = []
        game_id = 1

        while len(results) < num_games:
            result = self._run_with_retry(game_id, cop_fn, thief_fn)
            results.append(result)
            log.info(
                "Series progress: %d/%d — sub-game %d winner=%s",
                len(results), num_games, game_id, result.winner,
            )
            game_id += 1

        log.info("Full series complete. Results: %s", self.summarise(results))
        return results

    def _run_with_retry(
        self, game_id: int, cop_fn: AgentFn, thief_fn: AgentFn
    ) -> SubGameResult:
        """Run one sub-game, retrying up to _MAX_RERUN_ATTEMPTS on failure."""
        failures = 0
        while True:
            try:
                return SubGame(self._cfg, game_id, self._scorer).run(cop_fn, thief_fn)
            except TechnicalFailureError as exc:
                failures += 1
                log.warning(
                    "Sub-game %d technical failure #%d: %s — rerunning.",
                    game_id, failures, exc,
                )
                if failures >= _MAX_RERUN_ATTEMPTS:
                    raise RuntimeError(
                        f"Sub-game {game_id} failed {failures} times. Aborting."
                    ) from exc

    @staticmethod
    def summarise(results: list[SubGameResult]) -> ScoreSummary:
        """Return cumulative ScoreSummary across all results."""
        return Scorer.summarise(results)
