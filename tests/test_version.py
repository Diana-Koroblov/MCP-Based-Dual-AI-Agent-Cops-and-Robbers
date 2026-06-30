"""Tests for src.version — ensures VERSION is consistent across project files."""

from __future__ import annotations

import json
from pathlib import Path

from src.version import VERSION

_ROOT = Path(__file__).parent.parent
_CONFIG = _ROOT / "config" / "config.json"
_RATE = _ROOT / "config" / "rate_limits.json"


def test_version_is_string():
    assert isinstance(VERSION, str) and len(VERSION) > 0


def test_version_matches_config_json():
    data = json.loads(_CONFIG.read_text())
    assert data["version"] == VERSION, (
        f"config.json version '{data['version']}' != src/version.py '{VERSION}'"
    )


def test_version_matches_rate_limits_json():
    data = json.loads(_RATE.read_text())
    assert data["version"] == VERSION
