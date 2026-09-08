"""Native interactive-session tray client for LuxTime."""

from __future__ import annotations

import ctypes
import datetime
import os
from pathlib import Path
import shutil
import subprocess
import threading
import webbrowser

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("LOG_DIR", str(REPOSITORY_ROOT / "logs" / "tray"))

from foundry.logger import logger  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
import pystray  # noqa: E402

from tray.api_client import LuxTimeApi  # noqa: E402
from tray.idle import IdleDetector, windows_idle_seconds  # noqa: E402
from tray.runtime import TrayAlreadyRunningError, TrayRuntime  # noqa: E402

log = logger.bind(component="luxtime.tray")


class TrayApplication:
    def __init__(self, runtime: TrayRuntime) -> None:
        self.runtime = runtime
        self.api = LuxTimeApi()
        self.active: list[dict] = []
        self.projects: list[dict] = []
        self.application_name = "LuxTime"
        self.accent_color = "#22D3EE"
        self.connected = False
        self.connection_reported: bool | None = None
        self.idle_detector = IdleDetector()
        self.idle_error_reported = False
        self.lock = threading.Lock()
        self.stopping = threading.Event()
        self.icon = pystray.Icon(
            "LuxTime",
            self._icon_image(self.accent_color),
            self.application_name,
        )
        self.icon.menu = self._build_menu()

    @staticmethod
    def _icon_image(accent_color: str) -> Image.Image:
        try:
            accent = tuple(int(accent_color[index : index + 2], 16) for index in (1, 3, 5))
        except (TypeError, ValueError):
            accent = (34, 211, 238)
        image = Image.new("RGBA", (64, 64), (12, 12, 16, 255))
        draw = ImageDraw.Draw(image)
        draw.ellipse((10, 10, 54, 54), outline=(*accent, 255), width=5)
        draw.line((32, 19, 32, 34, 43, 40), fill=(226, 226, 236, 255), width=4)
        return image

    def _status_text(self) -> str:
        if not self.connected:
            return "● App unavailable"
        running = sum(1 for session in self.active if session["status"] == "running")
        paused = sum(1 for session in self.active if session["status"] == "paused")
        if running:
            return f"● Tracking · {running} project{'s' if running != 1 else ''}"
        if paused:
            return f"Ⅱ Paused · {paused} project{'s' if paused != 1 else ''}"
        return "● Running · No active work"

    def _call(self, callback) -> None:
        try:
            callback()
            self._refresh()
        except Exception as error:  # noqa: BLE001 - tray must remain usable when API is down
            log.warning("Tray API action failed", error_type=type(error).__name__)
            self.connected = False

    def _build_menu(self) -> pystray.Menu:
        with self.lock:
            active = list(self.active)
            projects = [project for project in self.projects if project["active"]]
            application_name = self.application_name

        def start_project(project_id: str):
            def callback(_icon, _item) -> None:
                self._call(lambda: self.api.start(project_id))

            return callback

        def session_action(session_id: str, action: str):
            def callback(_icon, _item) -> None:
                self._call(lambda: self.api.action(session_id, action))

            return callback

        start_items = [
            pystray.MenuItem(
                project["name"],
                start_project(str(project["id"])),
            )
            for project in projects
        ] or [pystray.MenuItem("No active projects", lambda *_: None, enabled=False)]

        session_items = []
        for session in active:
            action = "pause" if session["status"] == "running" else "resume"
            session_items.append(
                pystray.MenuItem(
                    f"{action.title()} {session['project']}",
                    session_action(str(session["id"]), action),
                )
            )
            session_items.append(
                pystray.MenuItem(
                    f"Stop {session['project']}",
                    session_action(str(session["id"]), "stop"),
                )
            )
        if not session_items:
            session_items.append(pystray.MenuItem("No active work", lambda *_: None, enabled=False))

        return pystray.Menu(
            pystray.MenuItem(self._status_text(), lambda *_: None, enabled=False),
            pystray.MenuItem(f"Open {application_name}", lambda *_: webbrowser.open(self.api.base_url), default=True),
            pystray.MenuItem("Start Project", pystray.Menu(*start_items)),
            pystray.MenuItem("Active Work", pystray.Menu(*session_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Pause All",
                lambda *_: self._call(lambda: self.api.action_all("pause")),
                enabled=any(session["status"] == "running" for session in active),
            ),
            pystray.MenuItem(
                "Resume All",
                lambda *_: self._call(lambda: self.api.action_all("resume")),
                enabled=any(session["status"] == "paused" for session in active),
            ),
            pystray.MenuItem(
                "Stop All",
                lambda *_: self._call(lambda: self.api.action_all("stop")),
                enabled=bool(active),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(f"Stop {application_name}", self._stop_luxtime),
            pystray.MenuItem("Exit Tray", self._exit_tray),
        )

    def _refresh(self) -> None:
        status = self.api.status()
        active = self.api.active()
        projects = self.api.projects()
        settings = self.api.settings()
        idle_stopped = self._apply_idle_policy(settings, active)
        if idle_stopped:
            status = self.api.status()
            active = self.api.active()
        application_name = settings.get("application_name", "LuxTime")
        accent_color = settings.get("accent_color", "#22D3EE")
        with self.lock:
            branding_changed = (
                application_name != self.application_name or accent_color != self.accent_color
            )
            self.connected = status.get("database_connected", False)
            self.active = active
            self.projects = projects
            self.application_name = application_name
            self.accent_color = accent_color
        if branding_changed:
            self.icon.title = application_name
            self.icon.icon = self._icon_image(accent_color)
            log.info(
                "Tray branding updated",
                application_name=application_name,
                accent_color=accent_color,
            )
        if self.connected != self.connection_reported:
            if self.connected:
                log.info("Tray connected to LuxTime API")
            else:
                log.warning("Tray reached LuxTime API but its database is unavailable")
            self.connection_reported = self.connected
        self.icon.menu = self._build_menu()
        self.icon.update_menu()

    def _apply_idle_policy(self, settings: dict, active: list[dict]) -> bool:
        enabled = bool(settings.get("idle_detection", False))
        threshold_minutes = int(settings.get("idle_threshold", 20))
        running = [session for session in active if session.get("status") == "running"]
        if not enabled:
            self.idle_detector.check(
                enabled=False,
                threshold_minutes=threshold_minutes,
                has_running_sessions=bool(running),
                idle_seconds=0,
            )
            return False
        if not running:
            return False
        try:
            idle_seconds = windows_idle_seconds()
            self.idle_error_reported = False
        except Exception as error:  # noqa: BLE001 - a tray poll must survive native API failure
            if not self.idle_error_reported:
                log.warning(
                    "Windows idle detection is unavailable",
                    error_type=type(error).__name__,
                )
                self.idle_error_reported = True
            return False

        trigger = self.idle_detector.check(
            enabled=enabled,
            threshold_minutes=threshold_minutes,
            has_running_sessions=bool(running),
            idle_seconds=idle_seconds,
        )
        if trigger is None:
            return False

        stopped = 0
        cutoff_at = trigger.cutoff_at.isoformat()
        for session in running:
            try:
                self.api.action(
                    str(session["id"]),
                    "stop",
                    at=cutoff_at,
                    reason="idle",
                )
                stopped += 1
            except Exception as error:  # noqa: BLE001 - retry remaining work on the next poll
                log.warning(
                    "Could not stop an idle session",
                    session_id=str(session.get("id")),
                    error_type=type(error).__name__,
                )

        if stopped != len(running):
            return stopped > 0

        self.idle_detector.mark_handled()
        log.info(
            "Stopped running sessions after Windows input became idle",
            idle_seconds=round(trigger.idle_seconds),
            idle_threshold_minutes=threshold_minutes,
            session_count=stopped,
            stopped_at=cutoff_at,
        )
        try:
            self.icon.notify(
                f"Stopped {stopped} running task{'s' if stopped != 1 else ''} after "
                f"{threshold_minutes} minutes without mouse or keyboard input.",
                self.application_name,
            )
        except Exception:  # noqa: BLE001 - notifications are optional
            pass
        return True

    def _poll(self) -> None:
        while not self.stopping.is_set():
            try:
                self._refresh()
            except Exception as error:  # noqa: BLE001 - connectivity is displayed, not fatal
                with self.lock:
                    self.connected = False
                    self.active = []
                if self.connection_reported is not False:
                    log.warning("Tray cannot connect to LuxTime API", error_type=type(error).__name__)
                    self.connection_reported = False
                self.icon.menu = self._build_menu()
                self.icon.update_menu()
            self.stopping.wait(5)

    @staticmethod
    def _docker_executable() -> str:
        discovered = shutil.which("docker")
        if discovered:
            return discovered
        program_files = os.getenv("ProgramFiles", r"C:\Program Files")
        return str(Path(program_files) / "Docker" / "Docker" / "resources" / "bin" / "docker.exe")

    def _stop_luxtime(self, *_: object) -> None:
        MB_YESNO = 0x00000004
        MB_ICONQUESTION = 0x00000020
        IDYES = 6
        with self.lock:
            application_name = self.application_name
        response = ctypes.windll.user32.MessageBoxW(
            None,
            f"Stop {application_name} and suppress watchdog restart until it is started again?",
            f"Stop {application_name}",
            MB_YESNO | MB_ICONQUESTION,
        )
        if response != IDYES:
            return
        runtime_root = REPOSITORY_ROOT / ".runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "intentional-stop").write_text(
            datetime.datetime.now(datetime.timezone.utc).isoformat(), encoding="utf-8"
        )
        subprocess.run(
            [
                self._docker_executable(),
                "compose",
                "--project-directory",
                str(REPOSITORY_ROOT),
                "-f",
                str(REPOSITORY_ROOT / "docker" / "compose.yml"),
                "down",
            ],
            cwd=REPOSITORY_ROOT,
            creationflags=subprocess.CREATE_NO_WINDOW,
            check=False,
        )
        self._exit_tray()

    def _exit_tray(self, *_: object) -> None:
        self.stopping.set()
        self.icon.stop()

    def run(self) -> None:
        self.runtime.watch_for_exit(self._exit_tray)
        threading.Thread(target=self._poll, name="luxtime-tray-poll", daemon=True).start()
        log.info("LuxTime tray started")
        try:
            self.icon.run()
        finally:
            self.stopping.set()
            self.runtime.close()
            log.info("LuxTime tray stopped")


def main() -> int:
    try:
        runtime = TrayRuntime()
    except TrayAlreadyRunningError:
        log.info("LuxTime tray start skipped because an instance is already running")
        return 0
    TrayApplication(runtime).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
