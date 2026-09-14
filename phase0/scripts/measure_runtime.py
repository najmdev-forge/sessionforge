#!/usr/bin/env python3
"""P0-05: compare test case runtime, distributed (from Linux) against local.

Runs the configured test case several times against the Windows host and
times it directly, that is the distributed measurement. For the local
baseline, either triggers the same command over SSH against the Windows
host itself (127.0.0.1) and times that SSH session, or accepts a manually
measured local duration as a fallback when SSH is not set up. Writes the
raw measurements to local/phase0/P0-05_<project>_raw.txt for later transfer
into ergebnisse/P0-05.md. Standard library only, ssh is called as an
external program, no Python SSH package is used.
"""

from __future__ import annotations

import argparse
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_config import load_config, require  # noqa: E402

COMMAND_KEYS = {
    "appium": "APPIUM_TESTCASE_CMD",
    "robot": "ROBOT_TESTCASE_CMD",
}
RESULTS_DIR = Path(__file__).resolve().parents[2] / "local" / "phase0"


def command_for(config: dict[str, str], project: str, host: str) -> str:
    (template,) = require(config, COMMAND_KEYS[project])
    return template.replace("{WINDOWS_HOST}", host)


def time_distributed(config: dict[str, str], project: str, runs: int) -> list[float]:
    (host,) = require(config, "WINDOWS_HOST")
    command = command_for(config, project, host)
    durations = []
    for i in range(1, runs + 1):
        print(f"Distributed run {i}/{runs}: {command}")
        start = time.monotonic()
        result = subprocess.run(command, shell=True)
        duration = time.monotonic() - start
        status = "OK" if result.returncode == 0 else "FAILED"
        print(f"  {status} in {duration:.2f}s")
        durations.append(duration)
    return durations


def time_local_via_ssh(config: dict[str, str], project: str, runs: int) -> list[float]:
    ssh_user, ssh_key_path = require(config, "SSH_USER", "SSH_KEY_PATH")
    (host,) = require(config, "WINDOWS_HOST")
    local_command = command_for(config, project, "127.0.0.1")

    durations = []
    for i in range(1, runs + 1):
        ssh_command = ["ssh", "-i", ssh_key_path, f"{ssh_user}@{host}", local_command]
        print(f"Local run {i}/{runs} via SSH: {local_command}")
        # Timed from this, the Linux, side, so the duration includes SSH
        # session overhead, not only the remote command itself.
        start = time.monotonic()
        result = subprocess.run(ssh_command)
        duration = time.monotonic() - start
        status = "OK" if result.returncode == 0 else "FAILED"
        print(f"  {status} in {duration:.2f}s")
        durations.append(duration)
    return durations


def summarize(label: str, durations: list[float]) -> None:
    mean = statistics.mean(durations)
    spread = statistics.stdev(durations) if len(durations) > 1 else 0.0
    print(f"{label}: mean {mean:.2f}s, stdev {spread:.2f}s, runs {durations}")


def write_raw_results(project: str, distributed: list[float], local: list[float]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"P0-05_{project}_raw.txt"
    lines = [
        f"project: {project}",
        f"distributed_runs_seconds: {distributed}",
        f"local_runs_seconds: {local}",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", choices=("appium", "robot"))
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument(
        "--local-duration",
        type=float,
        default=None,
        help="Manually measured local runtime in seconds, used instead of SSH.",
    )
    args = parser.parse_args()

    config = load_config()

    distributed = time_distributed(config, args.project, args.runs)

    if args.local_duration is not None:
        local = [args.local_duration]
        print(f"Using manually entered local duration: {args.local_duration:.2f}s")
    else:
        local = time_local_via_ssh(config, args.project, args.runs)

    summarize("Distributed", distributed)
    summarize("Local", local)

    deviation = statistics.mean(distributed) - statistics.mean(local)
    print(f"Deviation (distributed minus local): {deviation:.2f}s")

    out_path = write_raw_results(args.project, distributed, local)
    print(f"Raw values written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
