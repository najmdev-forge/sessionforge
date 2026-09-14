#!/usr/bin/env python3
"""P0-01 to P0-03: check that the Windows test services are reachable from Linux.

A TCP connect test for each port, an HTTP health check against Appium's
/status endpoint, and an XML-RPC call against the Robot Framework Remote
Library. With --service both (the default), both checks run at the same
time in separate threads, so this also covers P0-03, that neither service
blocks the other when both are used at once. Standard library only.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import http.client
import socket
import sys
import xmlrpc.client
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_config import load_config, require  # noqa: E402

TIMEOUT_SECONDS = 5


def check_tcp(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=TIMEOUT_SECONDS):
            return True
    except OSError as error:
        print(f"  TCP connect to {host}:{port} failed: {error}")
        return False


def check_appium_status(host: str, port: int, path: str) -> bool:
    connection = http.client.HTTPConnection(host, port, timeout=TIMEOUT_SECONDS)
    try:
        connection.request("GET", f"{path}/status")
        response = connection.getresponse()
        response.read()
        if response.status != 200:
            print(f"  Appium /status returned HTTP {response.status}")
            return False
        return True
    except OSError as error:
        print(f"  Appium /status request failed: {error}")
        return False
    finally:
        connection.close()


def check_robot_remote(host: str, port: int) -> bool:
    server = xmlrpc.client.ServerProxy(f"http://{host}:{port}/", allow_none=True)
    try:
        keywords = server.get_keyword_names()
        if not keywords:
            print("  Robot Remote Library returned no keywords")
            return False
        return True
    except (OSError, xmlrpc.client.Error) as error:
        print(f"  Robot Remote Library call failed: {error}")
        return False


def run_appium_check(config: dict[str, str]) -> bool:
    host, port_str = require(config, "WINDOWS_HOST", "APPIUM_PORT")
    path = config.get("APPIUM_PATH", "")
    port = int(port_str)
    print(f"Appium: TCP {host}:{port}")
    if not check_tcp(host, port):
        return False
    print(f"Appium: HTTP GET {path}/status")
    return check_appium_status(host, port, path)


def run_robot_check(config: dict[str, str]) -> bool:
    host, port_str = require(config, "WINDOWS_HOST", "ROBOT_REMOTE_PORT")
    port = int(port_str)
    print(f"Robot Framework Remote Library: TCP {host}:{port}")
    if not check_tcp(host, port):
        return False
    print("Robot Framework Remote Library: XML-RPC get_keyword_names")
    return check_robot_remote(host, port)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--service",
        choices=("appium", "robot", "both"),
        default="both",
        help="Which service to check. 'both' also covers P0-03.",
    )
    args = parser.parse_args()

    config = load_config()
    results: dict[str, bool] = {}

    if args.service == "both":
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_appium = executor.submit(run_appium_check, config)
            future_robot = executor.submit(run_robot_check, config)
            results["appium"] = future_appium.result()
            results["robot"] = future_robot.result()
    elif args.service == "appium":
        results["appium"] = run_appium_check(config)
    else:
        results["robot"] = run_robot_check(config)

    print()
    for service, ok in results.items():
        print(f"{service}: {'OK' if ok else 'FAILED'}")
    if args.service == "both":
        both_ok = all(results.values())
        print(f"both simultaneously reachable (P0-03): {'OK' if both_ok else 'FAILED'}")

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
