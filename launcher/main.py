"""Shortcut entry point: start LuxTime if needed, then open it in a browser.

Runs under the bundled interpreter with no dependencies beyond the standard
library, since it must work from a plain shortcut click with no venv/pip
setup step. Starting the service relies on the additional ACE that
``service.windows_service``'s ``ensure-installed`` verb grants Authenticated
Users at install time, so this never needs an elevated/UAC prompt.
"""

from __future__ import annotations

import subprocess
import time
import urllib.error
import urllib.request
import webbrowser

SERVICE_NAME = "LuxTimeService"
APP_URL = "http://127.0.0.1:52020"
HEALTH_URL = f"{APP_URL}/api/health"
HEALTH_TIMEOUT_SECONDS = 90
POLL_INTERVAL_SECONDS = 2


def _run_sc(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["sc.exe", *arguments],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
        check=False,
    )


def _service_running() -> bool:
    result = _run_sc("query", SERVICE_NAME)
    return "RUNNING" in result.stdout


def _is_healthy() -> bool:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=3) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False


def _wait_until_healthy(deadline: float) -> None:
    while time.monotonic() < deadline and not _is_healthy():
        time.sleep(POLL_INTERVAL_SECONDS)


def main() -> int:
    if not _service_running():
        _run_sc("start", SERVICE_NAME)
    _wait_until_healthy(time.monotonic() + HEALTH_TIMEOUT_SECONDS)
    webbrowser.open(APP_URL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
