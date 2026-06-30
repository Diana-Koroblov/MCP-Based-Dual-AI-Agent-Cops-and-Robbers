"""Agent action types and direction constants.

Why a dedicated module: actions are used by movement, strategy, orchestrator,
and tests — centralising them avoids circular imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = ["Direction", "ActionType", "AgentAction", "DIRECTION_DELTAS"]


class Direction(str, Enum):
    """Eight compass directions an agent may move."""

    N = "N"
    NE = "NE"
    E = "E"
    SE = "SE"
    S = "S"
    SW = "SW"
    W = "W"
    NW = "NW"


# Maps each direction to the (dx, dy) delta it applies to a position.
# (0,0) is top-left; x increases rightward, y increases downward.
DIRECTION_DELTAS: dict[Direction, tuple[int, int]] = {
    Direction.N: (0, -1),
    Direction.NE: (1, -1),
    Direction.E: (1, 0),
    Direction.SE: (1, 1),
    Direction.S: (0, 1),
    Direction.SW: (-1, 1),
    Direction.W: (-1, 0),
    Direction.NW: (-1, -1),
}


class ActionType(str, Enum):
    """The two actions an agent may take on its turn."""

    MOVE = "move"
    PLACE_BARRIER = "place_barrier"


@dataclass(frozen=True)
class AgentAction:
    """An immutable action chosen by an agent for a single turn.

    Attributes:
        action_type: Whether the agent moves or places a barrier.
        direction: Required when action_type is MOVE; ignored otherwise.
    """

    action_type: ActionType
    direction: Direction | None = None

    def __post_init__(self) -> None:
        if self.action_type == ActionType.MOVE and self.direction is None:
            raise ValueError("A MOVE action requires a direction.")
