"""Conservative Docker/application watchdog used by the Windows service."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
from urllib.error import URLError
from urllib.request import urlopen

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_CONFIG = REPOSITORY_ROOT / ".runtime" / "service-config.json"
os.environ.setdefault("LOG_DIR", str(REPOSITORY_ROOT / "logs" / "service"))

from foundry.logger import logger  # noqa: E402

log = logger.bind(component="luxtime.service")


def _default_docker_executable() -> str:
    configured = os.getenv("LUXTIME_DOCKER_EXE")
    if configured:
        return configured
    discovered = shutil.which("docker")
    if discovered:
        return discovered
    program_files = os.getenv("ProgramFiles", r"C:\Program Files")
    candidate = Path(program_files) / "Docker" / "Docker" / "resources" / "bin" / "docker.exe"
    return str(candidate)


@dataclass(frozen=True)
class WatchdogConfig:
    compose_file: Path = REPOSITORY_ROOT / "docker" / "compose.yml"
    intentional_stop_marker: Path = REPOSITORY_ROOT / ".runtime" / "intentional-stop"
    health_url: str = "http://127.0.0.1:52020/api/health"
    docker_executable: str = ""
    docker_host: str | None = None
    poll_seconds: float = 10.0
    recovery_wait_seconds: float = 10.0
    maximum_backoff_seconds: float = 300.0

    @classmethod
    def load(cls) -> "WatchdogConfig":
        values: dict[str, object] = {}
        if RUNTIME_CONFIG.is_file():
            try:
                values = json.loads(RUNTIME_CONFIG.read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                log.warning(
                    "Service runtime configuration could not be read",
                    error_type=type(error).__name__,
                )
        return cls(
            docker_executable=str(values.get("docker_executable") or _default_docker_executable()),
            docker_host=str(values["docker_host"]) if values.get("docker_host") else None,
        )


class LuxTimeWatchdog:
    container_names = ("luxtime-postgres", "luxtime-app")

    def __init__(self, config: WatchdogConfig | None = None) -> None:
        self.config = config or WatchdogConfig.load()
        self._last_docker_available: bool | None = None
        self._last_api_healthy: bool | None = None
        self._last_intentional_stop: bool | None = None
        self._last_container_states: dict[str, str] | None = None

    @staticmethod
    def _creation_flags() -> int:
        return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    def _docker_command(self, arguments: list[str]) -> list[str]:
        command = [self.config.docker_executable]
        if self.config.docker_host:
            command.extend(["--host", self.config.docker_host])
        command.extend(arguments)
        return command

    def _run_docker(self, arguments: list[str], *, timeout: float = 60) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                self._docker_command(arguments),
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                text=True,
                creationflags=self._creation_flags(),
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            log.warning(
                "Docker command could not run",
                command=arguments[0] if arguments else "unknown",
                error_type=type(error).__name__,
            )
            return subprocess.CompletedProcess(arguments, 1, "", "")

    def is_intentionally_stopped(self) -> bool:
        stopped = self.config.intentional_stop_marker.is_file()
        if stopped != self._last_intentional_stop:
            if stopped:
                log.info("Intentional stop marker present; watchdog recovery suppressed")
            elif self._last_intentional_stop is True:
                log.info("Intentional stop marker cleared; watchdog recovery enabled")
            self._last_intentional_stop = stopped
        return stopped

    def docker_available(self) -> bool:
        result = self._run_docker(["info"], timeout=15)
        available = result.returncode == 0
        if available != self._last_docker_available:
            if available:
                log.info("Docker engine available")
            else:
                log.warning("Docker engine unavailable")
            self._last_docker_available = available
        return available

    def container_states(self) -> dict[str, str]:
        states: dict[str, str] = {}
        template = "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}"
        for name in self.container_names:
            result = self._run_docker(["inspect", "--format", template, name], timeout=15)
            states[name] = result.stdout.strip() if result.returncode == 0 else "absent"
        if states != self._last_container_states:
            log.info("LuxTime container health changed", container_states=states)
            self._last_container_states = states
        return states

    def is_healthy(self) -> bool:
        healthy = False
        try:
            with urlopen(self.config.health_url, timeout=3) as response:
                payload = json.loads(response.read().decode("utf-8"))
                healthy = (
                    response.status == 200
                    and payload.get("status") == "healthy"
                    and payload.get("database") == "connected"
                )
        except (OSError, URLError, ValueError):
            healthy = False
        if healthy != self._last_api_healthy:
            if healthy:
                log.info("LuxTime API healthy")
            else:
                log.warning("LuxTime API unavailable")
            self._last_api_healthy = healthy
        return healthy

    def ensure_running(self, *, docker_ready: bool = False) -> bool:
        if self.is_intentionally_stopped():
            return False
        if not docker_ready and not self.docker_available():
            return False
        log.info("Ensuring LuxTime Compose stack is running")
        # Postgres is brought up on its own first: a cold `compose up -d` for
        # the whole stack races Compose's dependency-wait logic against
        # Postgres's own container creation and can silently drop Postgres's
        # published port. Creating it by itself first avoids that race; the
        # second call then finds it already running.
        postgres_result = self._run_docker(
            [
                "compose",
                "--project-directory",
                str(REPOSITORY_ROOT),
                "-f",
                str(self.config.compose_file),
                "up",
                "-d",
                "postgres",
            ],
            timeout=180,
        )
        if postgres_result.returncode != 0:
            log.error("LuxTime Postgres startup failed", exit_code=postgres_result.returncode)
            return False
        result = self._run_docker(
            [
                "compose",
                "--project-directory",
                str(REPOSITORY_ROOT),
                "-f",
                str(self.config.compose_file),
                "up",
                "-d",
            ],
            timeout=180,
        )
        if result.returncode != 0:
            log.error("LuxTime Compose startup failed", exit_code=result.returncode)
            return False
        log.info("LuxTime Compose start completed")
        self.container_states()
        return True

    def run(self, stop_event: threading.Event) -> None:
        backoff = self.config.poll_seconds
        log.info(
            "LuxTime watchdog started",
            docker_executable=self.config.docker_executable,
            docker_host_configured=bool(self.config.docker_host),
        )
        while not stop_event.is_set():
            if self.is_intentionally_stopped():
                backoff = self.config.poll_seconds
                stop_event.wait(self.config.poll_seconds)
                continue

            if not self.docker_available():
                log.warning("Waiting for Docker engine", retry_seconds=backoff)
                stop_event.wait(backoff)
                backoff = min(backoff * 2, self.config.maximum_backoff_seconds)
                continue

            self.container_states()
            if self.is_healthy():
                backoff = self.config.poll_seconds
                stop_event.wait(self.config.poll_seconds)
                continue

            log.warning("LuxTime unhealthy; attempting recovery")
            attempted = self.ensure_running(docker_ready=True)
            if attempted and stop_event.wait(self.config.recovery_wait_seconds):
                break
            if attempted:
                self.container_states()
                if self.is_healthy():
                    log.info("LuxTime recovery completed")
                    backoff = self.config.poll_seconds
                    continue

            log.warning("LuxTime remains unavailable", retry_seconds=backoff)
            stop_event.wait(backoff)
            backoff = min(backoff * 2, self.config.maximum_backoff_seconds)
        log.info("LuxTime watchdog stopped")
