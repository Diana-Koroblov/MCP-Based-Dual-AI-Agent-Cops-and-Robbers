"""Prompt builder — constructs per-turn agent prompts from game state.

Why here: prompt construction is complex enough to deserve its own module
and test suite. Centralising it means prompt changes never scatter across
the codebase. Templates are logged to docs/PROMPT_LOG.md.

Invariant enforced in every prompt:
    Agents must NEVER include numeric coordinates like (x, y) or [x, y].
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game.observed_state import ObservedState

__all__ = ["PromptBuilder"]

log = logging.getLogger(__name__)

# This instruction must appear verbatim in every prompt.
_NO_COORDS_INSTRUCTION = (
    "CRITICAL: Never include numeric coordinates such as (x,y) or [x,y] in your "
    "response. Describe positions using compass directions (N, S, E, W, NE, NW, SE, "
    "SW) and relative terms (ahead, behind, left, right, far, close)."
)


class PromptBuilder:
    """Builds structured turn prompts for the cop and thief agents.

    Args:
        grid_size: [rows, cols] of the board.
    """

    def __init__(self, grid_size: list[int]) -> None:
        self._rows, self._cols = grid_size

    def build(
        self,
        role: str,
        obs: ObservedState,
        received_message: str | None,
        belief_summary: str,
        valid_actions: list[str],
    ) -> str:
        """Construct a full turn prompt.

        Args:
            role: 'cop' or 'thief'.
            obs: The agent's current ObservedState.
            received_message: NL message from the opponent's last turn (may be None).
            belief_summary: Short text summary from BeliefState.
            valid_actions: List of valid action strings, e.g. ['N', 'E', 'place_barrier'].

        Returns:
            Full prompt string ready to send to the LLM.
        """
        sections = [
            self._role_section(role),
            self._state_section(obs),
            self._message_section(received_message),
            self._belief_section(belief_summary),
            self._actions_section(valid_actions),
            _NO_COORDS_INSTRUCTION,
            self._output_section(),
        ]
        prompt = "\n\n".join(s for s in sections if s)
        log.debug("Built prompt for %s (%d chars)", role, len(prompt))
        return prompt

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _role_section(self, role: str) -> str:
        if role == "cop":
            return (
                "You are the COP in a grid pursuit game. "
                "Your goal: capture the thief by moving to the same cell. "
                f"The board is {self._rows} rows × {self._cols} columns."
            )
        return (
            "You are the THIEF in a grid pursuit game. "
            "Your goal: survive as many turns as possible without being captured. "
            f"The board is {self._rows} rows × {self._cols} columns."
        )

    def _state_section(self, obs: ObservedState) -> str:
        parts = [
            f"Turn: {obs.move_count}",
            f"Your position: column {obs.own_pos[0]}, row {obs.own_pos[1]}",
            f"Barriers on board: {len(obs.known_barriers)}",
        ]
        if obs.barriers_remaining:
            parts.append(f"Barriers you may still place: {obs.barriers_remaining}")
        if obs.opponent_visible:
            op = obs.opponent_pos_if_visible
            parts.append(f"Opponent VISIBLE at column {op[0]}, row {op[1]}")  # type: ignore[index]
        else:
            parts.append("Opponent NOT visible (fog of war).")
        return "Current state:\n" + "\n".join(f"  • {p}" for p in parts)

    def _message_section(self, msg: str | None) -> str:
        if not msg:
            return ""
        return f'Message from opponent: "{msg}"'

    def _belief_section(self, summary: str) -> str:
        return f"Your belief about the opponent's location: {summary}"

    def _actions_section(self, actions: list[str]) -> str:
        return "Valid actions this turn: " + ", ".join(actions)

    def _output_section(self) -> str:
        return (
            "Respond with exactly two lines:\n"
            "ACTION: <one of the valid actions listed above>\n"
            "MESSAGE: <a short tactical message for your opponent (no coordinates)>"
        )
