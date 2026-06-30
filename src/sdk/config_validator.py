"""Config validator — runs at application startup.

Why here (not inline): centralising version checks means every entry-point
(CLI, GUI, tests) calls one function and gets a consistent error rather than
silently running with stale config values.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.version import VERSION

log = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "config.json"
_RATE_PATH = Path(__file__).parent.parent.parent / "config" / "rate_limits.json"


class ConfigVersionError(ValueError):
    """Raised when a config file's version does not match the application version."""


def _load_json(path: Path) -> dict:
    """Load and parse a JSON file, raising FileNotFoundError with a clear message."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open() as fh:
        return json.load(fh)


def _check_version(data: dict, path: Path) -> None:
    """Assert that *data* carries the expected version string."""
    file_version = data.get("version")
    if file_version != VERSION:
        raise ConfigVersionError(
            f"{path.name} has version '{file_version}' but application expects '{VERSION}'. "
            "Update the config file or src/version.py to match."
        )


def validate_config() -> tuple[dict, dict]:
    """Load, validate, and return (config, rate_limits) dicts.

    Raises:
        FileNotFoundError: if either config file is missing.
        ConfigVersionError: if either config file has the wrong version.
        KeyError: if a required key is absent from rate_limits.json.
    """
    config = _load_json(_CONFIG_PATH)
    rate_limits = _load_json(_RATE_PATH)

    _check_version(config, _CONFIG_PATH)
    _check_version(rate_limits, _RATE_PATH)

    _validate_rate_limits_keys(rate_limits)

    log.info("Config validated successfully (version %s)", VERSION)
    return config, rate_limits


_REQUIRED_RATE_KEYS = {
    "requests_per_minute",
    "max_queue_depth",
    "retry_delay_seconds",
    "max_retries",
}


def _validate_rate_limits_keys(rate_limits: dict) -> None:
    """Ensure all required rate-limit keys are present."""
    missing = _REQUIRED_RATE_KEYS - rate_limits.keys()
    if missing:
        raise KeyError(f"rate_limits.json is missing required keys: {sorted(missing)}")
