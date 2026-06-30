"""Single source of truth for the project version.

Why here: every module that needs the version imports this constant rather
than reading pyproject.toml at runtime (which would require importlib.metadata
and adds complexity). The config validator checks this value against config.json.
"""

VERSION = "1.00"
