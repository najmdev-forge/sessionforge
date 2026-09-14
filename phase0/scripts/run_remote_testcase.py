#!/usr/bin/env python3
"""P0-01 to P0-03: run one existing test case from Linux against the Windows host.

Takes the already working test invocation command from configuration and
runs it on this, the Linux, machine as the client, with the Windows target
host injected. Reports success or failure from the command's return code.
Run it once for P0-01 or P0-02, twice (appium and robot, one after another
or in two terminals) for P0-03. Standard library only.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_config import load_config, require  # noqa: E402

COMMAND_KEYS = {
    "appium": "APPIUM_TESTCASE_CMD",
    "robot": "ROBOT_TESTCASE_CMD",
}


def build_command(config: dict[str, str], project: str, override: str | None) -> str:
    if override:
        template = override
    else:
        (template,) = require(config, COMMAND_KEYS[project])
    (host,) = require(config, "WINDOWS_HOST")
    return template.replace("{WINDOWS_HOST}", host)


def run(project: str, override: str | None) -> int:
    config = load_config()
    (host,) = require(config, "WINDOWS_HOST")
    command = build_command(config, project, override)

    env = os.environ.copy()
    env["WINDOWS_HOST"] = host

    print(f"Running {project} test case against {host}:")
    print(f"  {command}")
    # The command comes from the user's own local/phase0/config.env, a
    # trusted local file, not external input, so shell=True is fine here.
    result = subprocess.run(command, shell=True, env=env)

    status = "OK" if result.returncode == 0 else "FAILED"
    print(f"{project}: {status} (exit code {result.returncode})")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", choices=("appium", "robot"))
    parser.add_argument(
        "--command",
        default=None,
        help="Override the configured test case command for this run.",
    )
    args = parser.parse_args()
    return run(args.project, args.command)


if __name__ == "__main__":
    raise SystemExit(main())
