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
from tray.runtime import TrayAlreadyRunningError, TrayRuntime  # noqa: E402

log = logger.bind(component="luxtime.tray")


class TrayApplication:
    def __init__(self, runtime: TrayRuntime) -> None:
        self.runtime = runtime
        self.api = LuxTimeApi()
        self.active: list[dict] = []
        self.projects: list[dict] = []
        self.connected = False
        self.connection_reported: bool | None = None
        self.lock = threading.Lock()
        self.stopping = threading.Event()
        self.icon = pystray.Icon("LuxTime", self._icon_image(), "LuxTime")
        self.icon.menu = self._build_menu()

    @staticmethod
    def _icon_image() -> Image.Image:
        image = Image.new("RGBA", (64, 64), (12, 12, 16, 255))
        draw = ImageDraw.Draw(image)
        draw.ellipse((10, 10, 54, 54), outline=(34, 211, 238, 255), width=5)
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

        start_items = [
            pystray.MenuItem(
                project["name"],
                lambda _icon, _item, project_id=str(project["id"]): self._call(
                    lambda: self.api.start(project_id)
                ),
            )
            for project in projects
        ] or [pystray.MenuItem("No active projects", lambda *_: None, enabled=False)]

        session_items = []
        for session in active:
            action = "pause" if session["status"] == "running" else "resume"
            session_items.append(
                pystray.MenuItem(
                    f"{action.title()} {session['project']}",
                    lambda _icon, _item, session_id=str(session["id"]), verb=action: self._call(
                        lambda: self.api.action(session_id, verb)
                    ),
                )
            )
            session_items.append(
                pystray.MenuItem(
                    f"Stop {session['project']}",
                    lambda _icon, _item, session_id=str(session["id"]): self._call(
                        lambda: self.api.action(session_id, "stop")
                    ),
                )
            )
        if not session_items:
            session_items.append(pystray.MenuItem("No active work", lambda *_: None, enabled=False))

        return pystray.Menu(
            pystray.MenuItem(self._status_text(), lambda *_: None, enabled=False),
            pystray.MenuItem("Open LuxTime", lambda *_: webbrowser.open(self.api.base_url), default=True),
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
            pystray.MenuItem("Stop LuxTime", self._stop_luxtime),
            pystray.MenuItem("Exit Tray", self._exit_tray),
        )

    def _refresh(self) -> None:
        status = self.api.status()
        active = self.api.active()
        projects = self.api.projects()
        with self.lock:
            self.connected = status.get("database_connected", False)
            self.active = active
            self.projects = projects
        if self.connected != self.connection_reported:
            if self.connected:
                log.info("Tray connected to LuxTime API")
            else:
                log.warning("Tray reached LuxTime API but its database is unavailable")
            self.connection_reported = self.connected
        self.icon.menu = self._build_menu()
        self.icon.update_menu()

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
        response = ctypes.windll.user32.MessageBoxW(
            None,
            "Stop the LuxTime application and suppress watchdog restart until it is started again?",
            "Stop LuxTime",
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
