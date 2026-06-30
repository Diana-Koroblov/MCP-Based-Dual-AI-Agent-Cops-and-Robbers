"""GameSDK — single public facade for the entire game.

Why a facade: GUI, CLI, and tests must never import from src.game,
src.orchestrator, or any other internal package directly. All access flows
through this class so that internal refactoring never breaks consumers.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.sdk.config_validator import validate_config
from src.sdk.game_sdk_reporting_mixin import ReportingMixin

if TYPE_CHECKING:
    from src.game.observed_state import ObservedState

log = logging.getLogger(__name__)

__all__ = ["GameSDK"]


class GameSDK(ReportingMixin):
    """Central entry-point for all game operations.

    Usage::

        sdk = GameSDK()
        sdk.start_game()
        while not sdk.is_game_over():
            obs = sdk.get_observed_state("cop")
            sdk.submit_action("cop", action)
    """

    def __init__(self) -> None:
        self._config, self._rate_limits = validate_config()
        self._full_game: object | None = None
        log.info("GameSDK initialised (version %s)", self._config["version"])

    # ------------------------------------------------------------------
    # Game lifecycle
    # ------------------------------------------------------------------

    def start_game(self) -> None:
        """Initialise and start a new 6-sub-game series."""
        from src.game.full_game import FullGame

        self._full_game = FullGame(self._config)
        log.info("Full game started.")

    def run(self) -> list:
        """Run all 6 sub-games and return the list of SubGameResult objects.

        Returns:
            List of exactly 6 SubGameResult dataclasses.
        """
        if self._full_game is None:
            raise RuntimeError("Call start_game() before run().")
        return self._full_game.run()  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    # Per-turn helpers (used by orchestrator / tests)
    # ------------------------------------------------------------------

    def get_observed_state(self, agent: str) -> ObservedState:
        """Return the current ObservedState for *agent* ('cop' or 'thief').

        Args:
            agent: Either 'cop' or 'thief'.

        Raises:
            ValueError: if *agent* is not 'cop' or 'thief'.
            RuntimeError: if no game is running.
        """
        if agent not in ("cop", "thief"):
            raise ValueError(f"agent must be 'cop' or 'thief', got '{agent}'")
        if self._full_game is None:
            raise RuntimeError("Call start_game() first.")
        return self._full_game.get_observed_state(agent)  # type: ignore[union-attr]

    def submit_action(self, agent: str, action: object) -> None:
        """Submit *action* for *agent* and advance the turn.

        Args:
            agent: 'cop' or 'thief'.
            action: An Action enum value (move direction or place_barrier).
        """
        if self._full_game is None:
            raise RuntimeError("Call start_game() first.")
        self._full_game.submit_action(agent, action)  # type: ignore[union-attr]

    def get_config(self) -> dict:
        """Return a copy of the loaded configuration dict."""
        return dict(self._config)
