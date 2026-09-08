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
from tray.power import PowerEvent, WindowsPowerMonitor  # noqa: E402
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
        self.away_prompted_ids: set[str] = set()
        self.pending_sleep_at: datetime.datetime | None = None
        self.power_lock = threading.Lock()
        self.power_monitor = WindowsPowerMonitor(self._on_power_event)
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
        sleeping = sum(1 for session in self.active if session.get("pause_mode") == "sleep")
        away = sum(1 for session in self.active if session.get("pause_mode") == "away")
        if running:
            return f"● Tracking · {running} project{'s' if running != 1 else ''}"
        if sleeping:
            return f"☾ Sleeping · {sleeping} project{'s' if sleeping != 1 else ''}"
        if away:
            return f"⌁ Away · {away} project{'s' if away != 1 else ''}"
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
            action_label = "Pause" if action == "pause" else "Wake" if session.get("pause_mode") == "sleep" else "Resume"
            session_items.append(
                pystray.MenuItem(
                    f"{action_label} {session['project']}",
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
        sleep_paused = self._apply_sleep_policy(settings, active)
        if sleep_paused:
            status = self.api.status()
            active = self.api.active()
        away_changed = self._apply_away_policy(settings, active)
        if away_changed:
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

    def _apply_away_policy(self, settings: dict, active: list[dict]) -> bool:
        enabled = bool(settings.get("idle_detection", False))
        threshold_minutes = int(settings.get("idle_threshold", 20))
        running = [session for session in active if session.get("status") == "running"]
        away = [session for session in active if session.get("pause_mode") == "away"]
        away_ids = {str(session["id"]) for session in away}
        self.away_prompted_ids.intersection_update(away_ids)
        if not enabled:
            self.idle_detector.check(
                enabled=False,
                threshold_minutes=threshold_minutes,
                has_running_sessions=bool(running),
                idle_seconds=0,
            )
            return self._prompt_to_resume_away(away, idle_seconds=0, threshold_minutes=threshold_minutes)
        if not running and not away:
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
            return self._prompt_to_resume_away(away, idle_seconds, threshold_minutes)

        paused = 0
        cutoff_at = trigger.cutoff_at.isoformat()
        for session in running:
            try:
                self.api.action(
                    str(session["id"]),
                    "pause",
                    at=cutoff_at,
                    mode="away",
                )
                paused += 1
            except Exception as error:  # noqa: BLE001 - retry remaining work on the next poll
                log.warning(
                    "Could not pause an away session",
                    session_id=str(session.get("id")),
                    error_type=type(error).__name__,
                )

        if paused != len(running):
            return paused > 0

        self.idle_detector.mark_handled()
        log.info(
            "Paused running sessions after Windows input became idle",
            idle_seconds=round(trigger.idle_seconds),
            idle_threshold_minutes=threshold_minutes,
            session_count=paused,
            paused_at=cutoff_at,
        )
        return True

    def _prompt_to_resume_away(
        self,
        away: list[dict],
        idle_seconds: float,
        threshold_minutes: int,
    ) -> bool:
        unprompted = [session for session in away if str(session["id"]) not in self.away_prompted_ids]
        if not unprompted or idle_seconds >= threshold_minutes * 60:
            return False

        count = len(unprompted)
        noun = "timer" if count == 1 else "timers"
        response = ctypes.windll.user32.MessageBoxW(
            None,
            f"Mouse or keyboard activity was detected.\n\nUnpause {count} away {noun}?",
            "Unpause timer?",
            0x00000004 | 0x00000020 | 0x00010000 | 0x00040000,
        )
        self.away_prompted_ids.update(str(session["id"]) for session in unprompted)
        if response != 6:
            log.info("Away resume prompt declined", session_count=count)
            return False

        resumed = 0
        for session in unprompted:
            try:
                self.api.action(str(session["id"]), "resume")
                resumed += 1
            except Exception as error:  # noqa: BLE001 - leave failed sessions safely paused
                log.warning(
                    "Could not resume an away session",
                    session_id=str(session.get("id")),
                    error_type=type(error).__name__,
                )
        log.info("Away sessions resumed after user confirmation", session_count=resumed)
        return resumed > 0

    def _on_power_event(self, event: PowerEvent) -> None:
        if event == "suspend":
            with self.power_lock:
                if self.pending_sleep_at is None:
                    self.pending_sleep_at = datetime.datetime.now(datetime.timezone.utc)
            log.info("Windows suspend detected")
        else:
            log.info("Windows resume detected")

    def _apply_sleep_policy(self, settings: dict, active: list[dict]) -> bool:
        with self.power_lock:
            suspend_at = self.pending_sleep_at
        if suspend_at is None:
            return False
        if not settings.get("stop_on_sleep", False):
            with self.power_lock:
                self.pending_sleep_at = None
            return False

        running = [session for session in active if session.get("status") == "running"]
        paused = 0
        for session in running:
            try:
                self.api.action(
                    str(session["id"]),
                    "pause",
                    at=suspend_at.isoformat(),
                    mode="sleep",
                )
                paused += 1
            except Exception as error:  # noqa: BLE001 - retry after resume or on the next poll
                log.warning(
                    "Could not put a session to sleep",
                    session_id=str(session.get("id")),
                    error_type=type(error).__name__,
                )

        if paused == len(running):
            with self.power_lock:
                self.pending_sleep_at = None
            log.info(
                "Paused running sessions for Windows sleep",
                session_count=paused,
                paused_at=suspend_at.isoformat(),
            )
        return paused > 0

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
        try:
            self.power_monitor.start()
            log.info("Windows power-event monitoring started")
        except Exception as error:  # noqa: BLE001 - tray and away detection remain useful
            log.warning("Windows power-event monitoring is unavailable", error_type=type(error).__name__)
        threading.Thread(target=self._poll, name="luxtime-tray-poll", daemon=True).start()
        log.info("LuxTime tray started")
        try:
            self.icon.run()
        finally:
            self.stopping.set()
            self.power_monitor.close()
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
