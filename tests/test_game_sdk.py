"""Tests for src.sdk.game_sdk.

Strategy: mock validate_config so we never touch the filesystem, then exercise
every error-path branch in GameSDK to push coverage above the 85% threshold.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.sdk.game_sdk import GameSDK

# ---------------------------------------------------------------------------
# Shared fixture — GameSDK with mocked config loading
# ---------------------------------------------------------------------------

@pytest.fixture
def sdk(minimal_config):
    """Return a GameSDK whose validate_config call is patched out."""
    rate_limits = {"version": "1.00", "requests_per_minute": 60}
    with patch("src.sdk.game_sdk.validate_config", return_value=(minimal_config, rate_limits)):
        yield GameSDK()


# ---------------------------------------------------------------------------
# get_config
# ---------------------------------------------------------------------------

def test_get_config_returns_expected_version(sdk, minimal_config):
    """get_config should return a dict containing the version key."""
    cfg = sdk.get_config()
    assert cfg["version"] == minimal_config["version"]


def test_get_config_returns_copy(sdk):
    """get_config must return a copy, not the internal dict."""
    assert sdk.get_config() is not sdk._config


# ---------------------------------------------------------------------------
# run() — before start_game
# ---------------------------------------------------------------------------

def test_run_before_start_raises(sdk):
    """run() must raise RuntimeError when called before start_game()."""
    with pytest.raises(RuntimeError, match="start_game"):
        sdk.run()


# ---------------------------------------------------------------------------
# get_observed_state — validation paths
# ---------------------------------------------------------------------------

def test_get_observed_state_invalid_agent_raises(sdk):
    """Unknown agent name must raise ValueError mentioning 'cop' and 'thief'."""
    with pytest.raises(ValueError, match="cop.*thief"):
        sdk.get_observed_state("referee")


def test_get_observed_state_no_game_raises(sdk):
    """get_observed_state raises RuntimeError when no game is running."""
    with pytest.raises(RuntimeError, match="start_game"):
        sdk.get_observed_state("cop")


def test_get_observed_state_thief_no_game_raises(sdk):
    """Same RuntimeError guard for the 'thief' agent."""
    with pytest.raises(RuntimeError, match="start_game"):
        sdk.get_observed_state("thief")


# ---------------------------------------------------------------------------
# submit_action — before start_game
# ---------------------------------------------------------------------------

def test_submit_action_no_game_raises(sdk):
    """submit_action raises RuntimeError when no game is running."""
    with pytest.raises(RuntimeError, match="start_game"):
        sdk.submit_action("cop", MagicMock())
