"""Scoring logic — per-sub-game results and cumulative series summary.

SubGameResult and ScoreSummary are frozen dataclasses so that the reporter
and GUI can pass them freely without risk of accidental mutation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

__all__ = ["SubGameResult", "ScoreSummary", "Scorer"]

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SubGameResult:
    """Result of one completed sub-game.

    Attributes:
        game_id: Sequential identifier (1-based).
        winner: 'cop' or 'thief'.
        moves: Number of turns taken.
        cop_score: Points awarded to the Cop this sub-game.
        thief_score: Points awarded to the Thief this sub-game.
        barriers_placed: Number of barriers the Cop placed.
        messages_exchanged: Total NL messages sent by both agents.
        technical_failures: Number of failed attempts before this valid result.
    """

    game_id: int
    winner: str
    moves: int
    cop_score: int
    thief_score: int
    barriers_placed: int
    messages_exchanged: int
    technical_failures: int


@dataclass(frozen=True)
class ScoreSummary:
    """Accumulated totals across all 6 sub-games."""

    cop_total_score: int
    thief_total_score: int
    cop_wins: int
    thief_wins: int
    technical_failures_total: int


class Scorer:
    """Computes per-sub-game scores and accumulates a ScoreSummary.

    Args:
        scoring_config: The 'scoring' dict from config.json.
    """

    def __init__(self, scoring_config: dict) -> None:
        self._cfg = scoring_config

    def compute(
        self,
        game_id: int,
        winner: str,
        moves: int,
        barriers_placed: int,
        messages_exchanged: int,
        technical_failures: int,
    ) -> SubGameResult:
        """Build a SubGameResult from raw sub-game data."""
        if winner == "cop":
            cop_score = self._cfg["cop_capture_points"]
            cop_score += barriers_placed * self._cfg.get("cop_per_barrier_points", 0)
            thief_score = 0
        else:
            cop_score = 0
            thief_score = self._cfg["thief_survival_points"]

        log.info(
            "Sub-game %d: winner=%s cop_score=%d thief_score=%d",
            game_id, winner, cop_score, thief_score,
        )
        return SubGameResult(
            game_id=game_id,
            winner=winner,
            moves=moves,
            cop_score=cop_score,
            thief_score=thief_score,
            barriers_placed=barriers_placed,
            messages_exchanged=messages_exchanged,
            technical_failures=technical_failures,
        )

    @staticmethod
    def summarise(results: list[SubGameResult]) -> ScoreSummary:
        """Aggregate a list of SubGameResult objects into a ScoreSummary."""
        return ScoreSummary(
            cop_total_score=sum(r.cop_score for r in results),
            thief_total_score=sum(r.thief_score for r in results),
            cop_wins=sum(1 for r in results if r.winner == "cop"),
            thief_wins=sum(1 for r in results if r.winner == "thief"),
            technical_failures_total=sum(r.technical_failures for r in results),
        )
