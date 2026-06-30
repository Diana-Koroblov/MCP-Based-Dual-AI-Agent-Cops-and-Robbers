"""Turn manager — applies one full turn (Thief then Cop) and checks win conditions.

Why separate from sub_game: turn logic (move application, win detection) is
unit-testable in isolation. sub_game.py then only needs to loop over turns
and handle technical failures.
"""

from __future__ import annotations

import logging
from enum import Enum

from src.game.actions import ActionType, AgentAction
from src.game.barriers import BarrierManager
from src.game.board import Board
from src.game.exceptions import InvalidActionError
from src.game.game_state import GameState
from src.game.movement import resolve_move

__all__ = ["TurnOutcome", "TurnManager"]

log = logging.getLogger(__name__)


class TurnOutcome(str, Enum):
    """Result of applying one full turn."""

    ONGOING = "ongoing"
    COP_WINS = "cop_wins"
    THIEF_WINS = "thief_wins"


class TurnManager:
    """Applies Thief→Cop actions each turn and detects win conditions.

    Args:
        initial_state: Starting GameState for this sub-game.
        board: Board instance (used for passability checks).
        barrier_mgr: Shared BarrierManager tracking the Cop's placements.
        max_moves: Maximum turns before the Thief wins by survival.
    """

    def __init__(
        self,
        initial_state: GameState,
        board: Board,
        barrier_mgr: BarrierManager,
        max_moves: int,
    ) -> None:
        self._state = initial_state
        self._board = board
        self._barrier_mgr = barrier_mgr
        self._max_moves = max_moves

    @property
    def state(self) -> GameState:
        """Current ground-truth game state."""
        return self._state

    def step(
        self, thief_action: AgentAction, cop_action: AgentAction
    ) -> TurnOutcome:
        """Apply one full turn: Thief moves, then Cop acts.

        Turn sequence:
        1. Apply Thief move.
        2. Apply Cop move OR Cop places barrier (barrier does not move Cop).
        3. If cop_pos == thief_pos → COP_WINS.
        4. Increment move_count. If move_count >= max_moves → THIEF_WINS.

        Raises:
            InvalidActionError: if Thief tries to place a barrier, or either
                agent chooses an impassable destination.
        """
        if thief_action.action_type == ActionType.PLACE_BARRIER:
            raise InvalidActionError("Thief cannot place barriers.")

        # Step 1 — Thief moves
        new_thief = resolve_move(
            self._state.thief_pos, thief_action, self._state.barriers, self._board
        )
        self._state = self._state.with_thief_pos(new_thief)

        # Step 2 — Cop acts
        if cop_action.action_type == ActionType.PLACE_BARRIER:
            placed = self._barrier_mgr.place(self._state.cop_pos)
            if placed:
                self._state = self._state.with_barrier(self._state.cop_pos)
        else:
            new_cop = resolve_move(
                self._state.cop_pos, cop_action, self._state.barriers, self._board
            )
            self._state = self._state.with_cop_pos(new_cop)

        # Step 3 — Win check: capture
        if self._state.cop_pos == self._state.thief_pos:
            log.info("Cop captured Thief at %s on move %d.", self._state.cop_pos,
                     self._state.move_count + 1)
            self._state = self._state.next_turn()
            return TurnOutcome.COP_WINS

        # Step 4 — Advance turn counter; check survival win
        self._state = self._state.next_turn()
        if self._state.move_count >= self._max_moves:
            log.info("Thief survived all %d moves — Thief wins.", self._max_moves)
            return TurnOutcome.THIEF_WINS

        return TurnOutcome.ONGOING
