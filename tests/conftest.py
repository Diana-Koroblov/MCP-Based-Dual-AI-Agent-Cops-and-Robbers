"""Shared pytest fixtures for the entire test suite.

Why here: fixtures defined in conftest.py are automatically available to every
test file without explicit imports. Centralising them avoids duplication and
ensures all tests use the same baseline game configuration.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# 1. Minimal config dict (mirrors config/config.json structure)
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_config() -> dict:
    """Return a minimal valid game configuration dictionary."""
    return {
        "version": "1.00",
        "student_id": "TEST_STUDENT",
        "grid_size": [5, 5],
        "max_moves": 25,
        "num_games": 6,
        "max_barriers": 5,
        "visibility_radius": 2,
        "llm_provider": "gemini",
        "llm_model": "gemini-1.5-flash",
        "cop_server_url": "http://localhost:8001",
        "thief_server_url": "http://localhost:8002",
        "scoring": {
            "cop_capture_points": 10,
            "thief_survival_points": 10,
        },
    }


# ---------------------------------------------------------------------------
# 2. Board factory (returns a fresh Board for each test)
# ---------------------------------------------------------------------------

@pytest.fixture
def board_5x5(minimal_config):
    """Return an initialised 5×5 Board instance."""
    from src.game.board import Board

    return Board(minimal_config["grid_size"])


# ---------------------------------------------------------------------------
# 3. ObservedState factory (callable fixture)
# ---------------------------------------------------------------------------

@pytest.fixture
def observed_state_factory():
    """Return a factory function that builds ObservedState objects.

    Usage::

        obs = observed_state_factory(own_pos=(0, 0))
    """
    from src.game.observed_state import ObservedState

    def _factory(
        own_pos: tuple = (0, 0),
        known_barriers: frozenset | None = None,
        opponent_visible: bool = False,
        opponent_pos_if_visible: tuple | None = None,
        move_count: int = 0,
        barriers_remaining: int = 5,
    ) -> ObservedState:
        return ObservedState(
            own_pos=own_pos,
            known_barriers=known_barriers or frozenset(),
            opponent_visible=opponent_visible,
            opponent_pos_if_visible=opponent_pos_if_visible,
            move_count=move_count,
            barriers_remaining=barriers_remaining,
        )

    return _factory


# ---------------------------------------------------------------------------
# 4. Mock Gemini client
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_gemini_client():
    """Return a MagicMock that mimics google.generativeai.GenerativeModel."""
    mock = MagicMock()
    mock.generate_content.return_value = MagicMock(
        text="I am heading north to cut off your escape route."
    )
    return mock


# ---------------------------------------------------------------------------
# 5. Mock MCP client
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_mcp_client():
    """Return a MagicMock that mimics src.orchestrator.client.MCPClient."""
    mock = MagicMock()
    mock.validate_position.return_value = {"valid": True, "reason": None}
    mock.send_message.return_value = {"success": True}
    mock.receive_message.return_value = {"message": None, "turn": None}
    return mock


# ---------------------------------------------------------------------------
# 6. SubGameResult factory
# ---------------------------------------------------------------------------

@pytest.fixture
def sub_game_result_factory():
    """Return a factory that builds SubGameResult dataclasses.

    Usage::

        result = sub_game_result_factory(winner="cop", moves=12)
    """
    from src.game.scorer import SubGameResult

    def _factory(
        game_id: int = 1,
        winner: str = "cop",
        moves: int = 10,
        cop_score: int = 10,
        thief_score: int = 0,
        barriers_placed: int = 2,
        messages_exchanged: int = 20,
        technical_failures: int = 0,
    ) -> SubGameResult:
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

    return _factory
