from __future__ import annotations

import json
from pathlib import Path
import subprocess

from service import watchdog as watchdog_module
from service.watchdog import LuxTimeWatchdog, WatchdogConfig


def _config(tmp_path: Path) -> WatchdogConfig:
    return WatchdogConfig(
        compose_file=tmp_path / "compose.yml",
        intentional_stop_marker=tmp_path / "intentional-stop",
        docker_executable="docker-test",
    )


def test_intentional_stop_suppresses_compose_recovery(tmp_path: Path) -> None:
    config = _config(tmp_path)
    config.intentional_stop_marker.write_text("test", encoding="utf-8")
    watchdog = LuxTimeWatchdog(config)

    def unexpected_docker_call(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess:
        raise AssertionError("Docker must not be called while intentionally stopped")

    watchdog._run_docker = unexpected_docker_call  # type: ignore[method-assign]

    assert watchdog.ensure_running() is False


def test_health_requires_api_and_database_health(tmp_path: Path, monkeypatch) -> None:
    watchdog = LuxTimeWatchdog(_config(tmp_path))

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"status": "healthy", "database": "connected"}).encode()

    monkeypatch.setattr(watchdog_module, "urlopen", lambda *_args, **_kwargs: Response())

    assert watchdog.is_healthy() is True


def test_recovery_uses_production_compose_file_and_configured_engine(tmp_path: Path) -> None:
    config = WatchdogConfig(
        compose_file=tmp_path / "compose.yml",
        intentional_stop_marker=tmp_path / "intentional-stop",
        docker_executable=r"C:\Docker\docker.exe",
        docker_host="npipe:////./pipe/dockerDesktopLinuxEngine",
    )
    watchdog = LuxTimeWatchdog(config)
    calls: list[list[str]] = []

    def successful_docker_call(arguments: list[str], **_kwargs: object) -> subprocess.CompletedProcess:
        calls.append(arguments)
        if arguments[0] == "inspect":
            return subprocess.CompletedProcess(arguments, 0, "healthy\n", "")
        return subprocess.CompletedProcess(arguments, 0, "", "")

    watchdog._run_docker = successful_docker_call  # type: ignore[method-assign]

    assert watchdog.ensure_running(docker_ready=True) is True
    assert calls[0] == [
        "compose",
        "--project-directory",
        str(watchdog_module.REPOSITORY_ROOT),
        "-f",
        str(config.compose_file),
        "up",
        "-d",
        "postgres",
    ]
    assert calls[1] == [
        "compose",
        "--project-directory",
        str(watchdog_module.REPOSITORY_ROOT),
        "-f",
        str(config.compose_file),
        "up",
        "-d",
    ]
    assert watchdog._docker_command(["info"]) == [
        r"C:\Docker\docker.exe",
        "--host",
        "npipe:////./pipe/dockerDesktopLinuxEngine",
        "info",
    ]
