"""Load phase0 configuration from local/phase0/config.env.

Standard library only. Configuration is read from exactly one place,
local/phase0/config.env, never searched for anywhere else.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "local" / "phase0" / "config.env"
EXAMPLE_PATH = REPO_ROOT / "phase0" / "config.example.env"


def _parse(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def load_config() -> dict[str, str]:
    if not CONFIG_PATH.exists():
        sys.exit(
            f"Missing {CONFIG_PATH}. Copy {EXAMPLE_PATH} to that path and fill "
            "in real values for this environment first."
        )
    return _parse(CONFIG_PATH)


def require(config: dict[str, str], *keys: str) -> list[str]:
    """Return the values for the given keys, or exit with a clear error."""
    missing = [key for key in keys if not config.get(key)]
    if missing:
        sys.exit(
            f"Missing value(s) in {CONFIG_PATH}: {', '.join(missing)}. "
            f"See {EXAMPLE_PATH} for the expected keys."
        )
    return [config[key] for key in keys]
