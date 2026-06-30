"""Tests for src.sdk.config_validator."""

from __future__ import annotations

import pytest

from src.sdk.config_validator import (
    ConfigVersionError,
    _check_version,
    _load_json,
    validate_config,
)
from src.version import VERSION

# ---------------------------------------------------------------------------
# _load_json
# ---------------------------------------------------------------------------

def test_load_json_missing_file(tmp_path):
    """Missing config file must raise FileNotFoundError with the path in the message."""
    missing = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError, match="missing.json"):
        _load_json(missing)


def test_load_json_valid(tmp_path):
    """Valid JSON file is parsed and returned as a dict."""
    f = tmp_path / "cfg.json"
    f.write_text('{"key": "value"}')
    assert _load_json(f) == {"key": "value"}


# ---------------------------------------------------------------------------
# _check_version
# ---------------------------------------------------------------------------

def test_check_version_matching(tmp_path):
    """No exception when version matches."""
    p = tmp_path / "cfg.json"
    _check_version({"version": VERSION}, p)  # must not raise


def test_check_version_mismatch(tmp_path):
    """ConfigVersionError raised when version does not match."""
    p = tmp_path / "cfg.json"
    with pytest.raises(ConfigVersionError, match="0.99"):
        _check_version({"version": "0.99"}, p)


def test_check_version_missing_key(tmp_path):
    """ConfigVersionError raised when 'version' key is absent."""
    p = tmp_path / "cfg.json"
    with pytest.raises(ConfigVersionError):
        _check_version({}, p)


# ---------------------------------------------------------------------------
# validate_config (integration — reads real files)
# ---------------------------------------------------------------------------

def test_validate_config_returns_dicts():
    """validate_config() returns two dicts with expected keys."""
    config, rate_limits = validate_config()
    assert "grid_size" in config
    assert "requests_per_minute" in rate_limits


def test_validate_config_version_correct():
    """Loaded configs carry the current application version."""
    config, rate_limits = validate_config()
    assert config["version"] == VERSION
    assert rate_limits["version"] == VERSION
